#!/usr/bin/env python3
"""Build and install a focused Blender bundle fixture; never connects to Blender.

Examples:
  python scripts/test-blender-agent.py --builder powershell
  python3 scripts/test-blender-agent.py --builder sh
  python scripts/test-blender-agent.py --builder sh --shell "C:/Program Files/Git/bin/bash.exe"
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
import tomllib


ROLE = "cs-blender-operator"
TREES = ("agents", ".codex/agents", ".gemini/agents", ".claude/agents", "plugins/claude/agents")
SKILLS = {"blender-mesh-editing", "blender-materials", "blender-textures",
          "blender-animation", "blender-camera"}
FRONT = re.compile(r"\A---\n.*?\n---\n", re.S)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def read(path):
    return path.read_text(encoding="utf-8-sig")


def check_bundle(agent_root, source_root):
    source_raw = read(source_root / f"{ROLE}.md")
    source_header = FRONT.match(source_raw)
    require(source_header is not None, f"Missing source frontmatter: {source_root / (ROLE + '.md')}")
    codex = agent_root.parent.name == ".codex"
    agent = agent_root / (f"{ROLE}.toml" if codex else f"{ROLE}.md")
    raw = read(agent)
    if codex:
        config = tomllib.loads(raw)
        for field in ("name", "description"):
            source_value = re.search(rf"^{field}:\s*(.+)$", source_header.group(), re.M).group(1).strip()
            if source_value.startswith('"'):
                source_value = json.loads(source_value)
            require(config[field] == source_value, f"Agent metadata changed: {agent}: {field}")
        require(config["model"] == "qwen-3.8-flash", f"Explicit model was replaced: {agent}")
        instructions = config["developer_instructions"]
        require("does not delegate to other personas" in instructions,
                f"Operator gained delegation instructions: {agent}")
        require(instructions.strip() == FRONT.sub("", source_raw).strip(),
                f"Agent body differs from source: {agent}")
        agent_text = instructions
    else:
        header = FRONT.match(raw)
        require(header is not None, f"Missing frontmatter: {agent}")
        for field in ("name", "description"):
            pattern = rf"^{field}:\s*(.+)$"
            require(re.search(pattern, header.group(), re.M).group(1)
                    == re.search(pattern, source_header.group(), re.M).group(1),
                    f"Agent metadata changed: {agent}: {field}")
        require(re.search(r"^model:\s*qwen-3\.8-flash\s*$", header.group(), re.M),
                f"Explicit model was replaced: {agent}")
        tools = re.search(r"^tools:\s*(.+)$", header.group(), re.M).group(1).split(",")
        tools = {tool.strip() for tool in tools}
        require(not any(tool == "Task" or tool.startswith("Agent") for tool in tools),
                f"Operator gained delegation tools: {agent}")
        for name in ("get_addon_status", "get_scene_info", "execute_blender_code", "look"):
            require(f"mcp__blender__{name}" in tools, f"Missing Blender operation: {agent}: {name}")
        require(FRONT.sub("", raw).strip() == FRONT.sub("", source_raw).strip(),
                f"Agent body differs from source: {agent}")
        agent_text = raw
    bundle = agent_root / ROLE
    require({p.parent.name for p in bundle.rglob("SKILL.txt")} == SKILLS,
            f"Missing or extra private skill: {bundle}")
    require(not list(bundle.rglob("*.md")), f"Private resource can register as an agent: {bundle}")
    source_files = [p for p in (source_root / ROLE).rglob("*") if p.is_file()]
    manifest = dict(line.split(" ", 1)[::-1] for line in
                    read(agent_root / ".agent-resources-manifest").splitlines() if line)
    for src in source_files:
        relative = src.relative_to(source_root)
        require((agent_root / relative).read_bytes() == src.read_bytes(),
                f"Private resource changed during packaging: {relative}")
        require(manifest.get(relative.as_posix()) == hashlib.sha256(src.read_bytes()).hexdigest(),
                f"Private resource ownership missing: {relative}")
    documents = [(agent, agent_text)] + [
        (bundle / p.relative_to(source_root / ROLE), read(bundle / p.relative_to(source_root / ROLE)))
        for p in source_files
    ]
    for doc, content in documents:
        for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
            if re.match(r"^[a-z]+://|^#", link):
                continue
            require((doc.parent / link.split("#")[0]).resolve().is_file(),
                    f"Broken installed resource link: {doc}: {link}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--builder", choices=("powershell", "sh"), required=True)
    parser.add_argument("--shell", help="Override the builder's shell executable")
    parser.add_argument("--keep", action="store_true", help="Keep the isolated build for inspection")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent.parent
    shell = args.shell or shutil.which(args.builder)
    require(shell, f"Shell unavailable: {args.builder}; supply --shell")
    workspace = Path(tempfile.mkdtemp(prefix="myskills-blender-test-")).resolve()
    try:
        root = workspace / "build"
        root.mkdir()
        for rel in ("scripts", ".claude/rules", ".codebuddy/references"):
            if (repo / rel).exists():
                shutil.copytree(repo / rel, root / rel)
        source = root / ".codebuddy/agents"
        source.mkdir(parents=True)
        shutil.copy2(repo / ".codebuddy/agents" / f"{ROLE}.md", source)
        shutil.copytree(repo / ".codebuddy/agents" / ROLE, source / ROLE)
        # One existing role/skill checks coexistence without rebuilding unrelated asset bundles.
        shutil.copy2(repo / ".codebuddy/agents/cs-test-engineer.md", source)
        shutil.copytree(repo / ".codebuddy/skills/cs-minimal", root / ".codebuddy/skills/cs-minimal")
        (root / ".codebuddy/commands").mkdir()
        shutil.copy2(repo / ".codebuddy/commands/cs-build.md", root / ".codebuddy/commands")
        # Emulate a POSIX checkout when testing Git Bash from a CRLF Windows checkout.
        if args.builder == "sh":
            for script in (root / "scripts").rglob("*.sh"):
                script.write_bytes(script.read_bytes().replace(b"\r\n", b"\n"))

        def run(script, *arguments):
            extension = "ps1" if args.builder == "powershell" else "sh"
            command = [shell]
            if args.builder == "powershell":
                command += ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File"]
            command += [f"scripts/{script}.{extension}", *arguments]
            with tempfile.TemporaryFile() as log:
                result = subprocess.run(command, cwd=root, stdout=log,
                                        stderr=subprocess.STDOUT, timeout=240)
                log.seek(0)
                output = log.read().decode(errors="replace")
            require(result.returncode == 0, f"{script} failed ({result.returncode}):\n{output[-6000:]}")

        run("build-adapters")
        for tree in TREES:
            check_bundle(root / tree, source)
        for tree in ("skills", ".agents/skills", ".gemini/skills", ".claude/skills", "plugins/claude/skills"):
            require(not any(p.name in SKILLS or p.name == ROLE for p in (root / tree).iterdir()),
                    f"Private skill exposed publicly: {tree}")
        print("PASS: five adapter trees preserve the explicit model, tools, bundle bytes and links.", flush=True)

        destination = workspace / "installed project"
        if args.builder == "powershell":
            install_args = ("-Target", "claude", "-Destination", str(destination), "-Merge")
        else:
            # Relative paths work in both native POSIX shells and Git Bash on Windows.
            install_args = ("--target", "claude", "--destination", "../installed project")
        run("install", *install_args)
        for tree in (".claude/agents", "plugins/claude/agents"):
            check_bundle(destination / tree, source)
        local = destination / ".claude/agents" / ROLE / "skills/blender-textures/SKILL.txt"
        local.write_bytes(local.read_bytes() + b"\nUser customization for this installation.\n")
        edited = local.read_bytes()
        user_file = local.parent / "user-notes.txt"
        user_file.write_text("Keep my notes.\n", encoding="utf-8")
        run("install", *install_args)
        require(local.read_bytes() == edited, "Reinstallation overwrote a customized private skill")
        require(read(user_file) == "Keep my notes.\n", "Reinstallation removed user-owned content")
        print("PASS: project/plugin installation works; reinstallation preserves user edits.", flush=True)
    finally:
        if args.keep:
            print(f"Workspace: {workspace}", flush=True)
        else:
            require(workspace.parent == Path(tempfile.gettempdir()).resolve()
                    and workspace.name.startswith("myskills-blender-test-"), "Unsafe cleanup path")
            shutil.rmtree(workspace)


if __name__ == "__main__":
    main()
