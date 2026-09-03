"""Keep the working-tree diff focused on the new skill.

Running the adapter build regenerates every generated tree. Two classes of
diff come along for the ride and carry no meaning for this change:

1. Junk paths under `plugins/claude/skills/` — an older build script
   accumulated `$dst` per skill, committing nested duplicate skill trees
   (e.g. plugins/claude/skills/cs-api-design/cs-browser-test/SKILL.md).
   A correct build deletes them. Restore so this change stays scoped.
2. BOM / trailing-newline differences — some generated files were committed
   from the POSIX script (no BOM, trailing newline) and some from Windows
   PowerShell 5.1 (BOM, no trailing newline). Restore when that is the only
   difference.
"""

import subprocess

BOM = b"\xef\xbb\xbf"


def git(*args):
    return subprocess.run(["git"] + list(args), capture_output=True).stdout


def status_paths():
    """Return [(xy, path)] using -z so non-ASCII paths are not quoted."""
    raw = git("status", "--porcelain", "-z").decode("utf-8")
    out = []
    for rec in raw.split("\0"):
        if not rec:
            continue
        out.append((rec[:2], rec[3:]))
    return out


def strip_bom(data):
    return data[3:] if data.startswith(BOM) else data


def normalize(data):
    return strip_bom(data).rstrip(b"\r\n")


def checkout(paths):
    if not paths:
        return
    for i in range(0, len(paths), 80):
        subprocess.run(["git", "checkout", "--"] + paths[i:i + 80], check=True)


# 1. Restore the nested duplicate skill trees committed by an older build.
entries = status_paths()
junk = sorted({p for _, p in entries
               if p.startswith("plugins/claude/") and p.count("/cs-") > 1})
print("restoring junk paths:", len(junk))
checkout(junk)

# 2. Revert BOM / trailing-newline-only changes.
modified = [p for xy, p in status_paths() if xy == " M"]
noise = []
for path in modified:
    try:
        with open(path, "rb") as fh:
            work = fh.read()
    except OSError:
        continue
    if normalize(git("show", "HEAD:" + path)) == normalize(work):
        noise.append(path)

print("reverting whitespace/BOM-only:", len(noise))
checkout(noise)

remaining = sorted(p for _, p in status_paths())
print("remaining changed files:", len(remaining))
for path in remaining:
    print(" ", path)
