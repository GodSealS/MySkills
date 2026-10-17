"""Dispatch survives valid frontmatter ordering and exact tool-token rewrites."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which('bash') if os.name != 'nt' else r'C:\Program Files\Git\bin\bash.exe'


class CocosDispatchAdapters(unittest.TestCase):
    def exercise(self, shell):
        with tempfile.TemporaryDirectory(prefix='cocos-dispatch-') as tmp:
            repo = Path(tmp)
            for name in ('scripts', '.claude/rules'):
                shutil.copytree(ROOT / name, repo / name)
            source = repo / '.codebuddy'
            for directory in ('agents', 'commands', 'references'):
                (source / directory).mkdir(parents=True)
            shutil.copytree(ROOT / '.codebuddy/skills/cs-minimal', source / 'skills/cs-minimal')
            (source / 'references/probe.md').write_text('Fixture reference.\n')
            (source / 'commands/probe.md').write_text('---\ndescription: Fixture\n---\nUse cs-minimal.\n')
            cases = {
                # tools deliberately precedes name; Task appears at either end.
                'cs-frontend-lead': ('Task, Read, Bash', 'Agent(cs-cocos-specialist), Read, Bash'),
                'cs-backend-lead': ('Read, Bash, Task', 'Read, Bash, Agent(cs-network-programmer)'),
                # Removing a middle token must preserve separators and other names.
                'cs-code-reviewer': ('Read, Task, Bash, TaskOutput', 'Read, Bash, TaskOutput'),
                'cs-cocos-specialist': ('Read, Bash', 'Read, Bash'),
                'cs-network-programmer': ('Read, Bash', 'Read, Bash'),
            }
            body = ('# Fixture\n\n---\nExample:\n\ntools: Task, Read\n'
                    'tools: Agent(cs-cocos-specialist), Agent(cs-network-programmer)\n---\n')
            for name, (tools, _) in cases.items():
                raw = (f'---\ntools: {tools}\nname: {name}\ndescription: Fixture\n'
                       f'model: DeepSeek-V4-Pro\n---\n{body}')
                if name == 'cs-backend-lead':
                    raw = raw.replace('\n', '\r\n')
                (source / f'agents/{name}.md').write_bytes(raw.encode('utf-8'))
            command = (['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                        str(repo / 'scripts/build-adapters.ps1')] if shell == 'ps1'
                       else [BASH, str(repo / 'scripts/build-adapters.sh')])
            result = subprocess.run(command, cwd=repo, capture_output=True, text=True,
                                    encoding='utf-8', errors='replace', timeout=300)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for target in ('.claude/agents', 'plugins/claude/agents'):
                for name, (_, expected) in cases.items():
                    with self.subTest(target=target, name=name):
                        raw = (repo / target / f'{name}.md').read_text(encoding='utf-8-sig')
                        if target.startswith('plugins/'):
                            expected = expected.replace('Agent(cs-', 'Agent(agent-skills-cs:cs-')
                        actual = re.search(r'^tools: (.+)$', raw, re.MULTILINE).group(1)
                        self.assertEqual(actual, expected)
                        self.assertEqual(raw.split('---\n', 2)[2], body)

    @unittest.skipUnless(shutil.which('powershell'), 'PowerShell is not installed')
    def test_powershell(self):
        self.exercise('ps1')

    @unittest.skipUnless(BASH and (Path(BASH).is_file() or shutil.which(BASH)), 'POSIX shell is not installed')
    def test_posix(self):
        self.exercise('sh')


if __name__ == '__main__':
    unittest.main()
