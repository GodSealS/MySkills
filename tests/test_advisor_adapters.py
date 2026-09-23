"""Private persona resources survive builds and safe project/global upgrades."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which("bash") if os.name != "nt" else r"C:\Program Files\Git\bin\bash.exe"


class AdvisorAdapters(unittest.TestCase):
    def exercise(self, shell):
        with tempfile.TemporaryDirectory(prefix="advisor-adapters-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            for name in (".codebuddy", "scripts", ".claude/rules"):
                shutil.copytree(ROOT / name, repo / name)
            for name in ('AGENTS.md', 'GEMINI.md', 'CLAUDE.md'):
                shutil.copyfile(ROOT / name, repo / name)
            # Resource tests need one public skill; the full adapter harness
            # separately exercises every skill. Keep POSIX process cost bounded.
            for skill in (repo / '.codebuddy/skills').iterdir():
                if skill.name != 'cs-minimal':
                    shutil.rmtree(skill)
            for reference in list((repo / '.codebuddy/references').iterdir())[1:]:
                if reference.is_file() and reference.name != 'cs-user-context.md':
                    reference.unlink()
            for command in (repo / '.codebuddy/commands').glob('*.md'):
                command.unlink()
            (repo / '.codebuddy/commands/probe.md').write_text('---\ndescription: Resource fixture\n---\nUse cs-minimal.\n')
            for persona in (repo / '.codebuddy/agents').glob('*.md'):
                persona.unlink()
            agent = repo / ".codebuddy/agents/cs-review-advisor.md"
            agent.write_text("---\nname: cs-review-advisor\nmodel: DeepSeek-V4-Pro\n---\n# Advisor\n", encoding="utf-8")
            bundle = agent.with_suffix("")
            bundle.mkdir(exist_ok=True)
            resource = bundle / "skills/probe/SKILL.txt"
            resource.parent.mkdir(parents=True, exist_ok=True)
            resource.write_text("---\nname: private-probe\nmodel: untouched\n---\nPrivate bytes\n", encoding="utf-8")
            edited = resource.with_name('edited.txt')
            edited.write_text('original')
            def run(script, *args):
                cmd = (["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(repo / "scripts" / (script + ".ps1"))]
                       if shell == "ps1" else [BASH, str(repo / "scripts" / (script + ".sh"))])
                result = subprocess.run(cmd + list(args), cwd=tmp, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            run("build-adapters")
            for target, model in (("agents", "DeepSeek-V4-Pro"), (".codex/agents", "gpt-5.6-sol"), (".gemini/agents", "gemini-2.5-pro"), (".claude/agents", "opus"), ("plugins/claude/agents", "opus")):
                self.assertIn("model: " + model, (repo / target / agent.name).read_text(encoding="utf-8-sig"))
                self.assertEqual((repo / target / "cs-review-advisor/skills/probe/SKILL.txt").read_bytes(), resource.read_bytes())
                self.assertEqual(list((repo / target / 'cs-review-advisor').rglob('*.md')), [])
            for public in ("skills", ".agents/skills", ".gemini/skills", ".claude/skills"):
                self.assertFalse((repo / public / "probe").exists())
            installs = []
            for global_install in (False, True):
                dest = Path(tmp) / ("global" if global_install else "project")
                dest.mkdir()
                args = ["-Target", "all", "-Destination", str(dest)] if shell == "ps1" else ["--target", "all", "--destination", str(dest)]
                if global_install:
                    args += ["-UserHome", "-UserHomePath", str(dest)] if shell == "ps1" else ["--user-home", "--user-home-path", str(dest)]
                run("install", *args)
                context = dest / ('.codex/AGENTS.md' if global_install else 'AGENTS.md')
                expected_context = repo / ('.codebuddy/references/cs-user-context.md' if global_install else 'AGENTS.md')
                self.assertEqual(context.read_text(encoding='utf-8-sig'), expected_context.read_text(encoding='utf-8-sig'))
                if global_install:
                    self.assertFalse((dest / 'AGENTS.md').exists())
                installs.append((dest, args))
                for platform in (".codebuddy", ".gemini", ".codex", ".claude"):
                    installed = dest / platform / "agents/cs-review-advisor"
                    self.assertEqual((installed / "skills/probe/SKILL.txt").read_bytes(), resource.read_bytes())
                    (installed / "user.txt").write_text("mine")
                    (installed / "skills/probe/edited.txt").write_text("mine")
            for agents in ("agents", ".gemini/agents", ".codex/agents", ".claude/agents", "plugins/claude/agents"):
                (repo / agents / "cs-review-advisor/user.txt").write_text("mine")
            resource.rename(resource.with_name("renamed.txt"))
            edited.write_text('upstream revision')
            stale_plugin = repo / 'plugins/claude/skills/stale.txt'
            stale_plugin.write_text('stale generated output')
            run("build-adapters")
            if shell == 'ps1':
                self.assertFalse(stale_plugin.exists())
            for agents in ("agents", ".gemini/agents", ".codex/agents", ".claude/agents", "plugins/claude/agents"):
                self.assertFalse((repo / agents / "cs-review-advisor/skills/probe/SKILL.txt").exists())
                self.assertEqual((repo / agents / "cs-review-advisor/user.txt").read_text(), "mine")
            for dest, args in installs:
                run("install", *args)
                for platform in (".codebuddy", ".gemini", ".codex", ".claude"):
                    installed = dest / platform / "agents/cs-review-advisor"
                    self.assertFalse((installed / "skills/probe/SKILL.txt").exists())
                    self.assertTrue((installed / "skills/probe/renamed.txt").exists())
                    self.assertEqual((installed / "user.txt").read_text(), "mine")
                    self.assertEqual((installed / "skills/probe/edited.txt").read_text(), "mine")
            if shell == 'ps1':
                project = installs[0][0]
                stale = project / '.gemini/skills/stale.txt'
                stale.write_text('obsolete')
                run('install', '-Target', 'gemini', '-Destination', str(project), '-Clean')
                self.assertFalse(stale.exists())
                self.assertEqual((project / '.gemini/agents/cs-review-advisor/user.txt').read_text(), 'mine')
                self.assertEqual((project / '.gemini/agents/cs-review-advisor/skills/probe/edited.txt').read_text(), 'mine')

    @unittest.skipUnless(shutil.which('powershell'), 'PowerShell is not installed')
    def test_powershell(self):
        self.exercise("ps1")

    @unittest.skipUnless(BASH and (Path(BASH).is_file() or shutil.which(BASH)), 'POSIX shell is not installed')
    def test_posix(self):
        self.exercise("sh")


if __name__ == "__main__":
    unittest.main()
