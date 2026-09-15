"""Exercise resource ownership deletion and malicious manifests in isolation."""
import os
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = r'C:\Program Files\Git\bin\bash.exe' if os.name == 'nt' else 'bash'


def directory_link(target, link):
    if os.name == 'nt':
        result = subprocess.run(['powershell', '-NoProfile', '-Command', "New-Item -ItemType Junction -Path '" + str(link) + "' -Target '" + str(target) + "' | Out-Null"], capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise RuntimeError(result.stderr)
    else:
        os.symlink(target, link, target_is_directory=True)


def remove_directory_link(link):
    if os.name == 'nt':
        os.rmdir(link)
    else:
        link.unlink()


class ResourceSafety(unittest.TestCase):
    def exercise(self, shell):
        with tempfile.TemporaryDirectory(prefix='resource-safety-') as tmp:
            base = Path(tmp)
            src, dst = base / 'source', base / 'destination'
            src.mkdir()
            dst.mkdir()
            (src / 'persona.md').write_text('persona')
            (src / 'persona').mkdir()
            (src / 'persona/old.txt').write_text('old')
            def run():
                if shell == 'ps1':
                    wrapper = base / 'run.ps1'
                    wrapper.write_text("$ErrorActionPreference = 'Stop'\n. '" + str(ROOT / 'scripts/agent-resources.ps1') + "'\nSync-AgentResources '" + str(src) + "' '" + str(dst) + "'\n")
                    cmd = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(wrapper)]
                else:
                    wrapper = base / 'run.sh'
                    wrapper.write_text("set -eu\n. '" + (ROOT / 'scripts/agent-resources.sh').as_posix() + "'\nsync_agent_resources '" + src.as_posix() + "' '" + dst.as_posix() + "'\n")
                    cmd = [BASH, str(wrapper)]
                return subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            result = run()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            (dst / 'persona/user.txt').write_text('mine')
            (src / 'persona.md').unlink()
            result = run()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse((dst / 'persona/old.txt').exists())
            self.assertEqual((dst / 'persona/user.txt').read_text(), 'mine')
            outside = base / 'outside.txt'
            outside.write_text('keep')
            manifest = dst / '.agent-resources-manifest'
            manifest.write_text('0' * 64 + ' ../outside.txt\n')
            self.assertNotEqual(run().returncode, 0)
            self.assertEqual(outside.read_text(), 'keep')
            manifest.unlink()
            # NTFS junctions require no symlink privilege and exercise the same
            # reparse-point refusal before the manifest is read or written.
            directory_link(base, manifest)
            try:
                result = run()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('contains a link', result.stdout + result.stderr)
                self.assertEqual(outside.read_text(), 'keep')
            finally:
                remove_directory_link(manifest)
            if shell == 'ps1':
                repo = base / 'repo'
                (repo / 'scripts').mkdir(parents=True)
                (repo / '.gemini/agents').mkdir(parents=True)
                for name in ('install.ps1', 'agent-resources.ps1'):
                    shutil.copyfile(ROOT / 'scripts' / name, repo / 'scripts' / name)
                project = base / 'project'
                project.mkdir()
                external = base / 'external'
                external.mkdir()
                (external / 'keep.txt').write_text('keep')
                link = project / '.gemini'
                directory_link(external, link)
                try:
                    result = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(repo / 'scripts/install.ps1'), '-Target', 'gemini', '-Destination', str(project), '-Clean'], capture_output=True, text=True, timeout=30)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual((external / 'keep.txt').read_text(), 'keep')
                finally:
                    remove_directory_link(link)

    @unittest.skipUnless(shutil.which('powershell'), 'PowerShell is not installed')
    def test_powershell_safety(self):
        self.exercise('ps1')

    @unittest.skipUnless(BASH and (Path(BASH).is_file() or shutil.which(BASH)), 'POSIX shell is not installed')
    def test_posix_safety(self):
        self.exercise('sh')


if __name__ == '__main__':
    unittest.main()
