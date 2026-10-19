#!/usr/bin/env python3
"""Isolated build/install and Forge smoke checks; no browser or Blender connection."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib


SKILL = 'cs-img2threejs'
TREES = ('skills', '.agents/skills', '.gemini/skills', '.claude/skills', 'plugins/claude/skills')


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resource_digest(path):
    raw = path.read_bytes()
    try:
        raw.decode('utf-8')
        if b'\x00' not in raw:
            raw = raw.replace(b'\r\n', b'\n')
    except UnicodeDecodeError:
        pass
    return hashlib.sha256(raw).hexdigest()


def verify_bundle(bundle):
    provenance = json.loads((bundle / 'PROVENANCE.json').read_text(encoding='utf-8'))
    for rel, expected in provenance['files_sha256'].items():
        require((bundle / rel).is_file(), f'Missing runtime resource: {bundle / rel}')
        require(resource_digest(bundle / rel) == expected, f'Changed upstream resource: {bundle / rel}')
    for rel, record in provenance.get('adapted_files', {}).items():
        require(re.fullmatch(r'[0-9a-f]{64}', record['upstream_sha256']),
                f'Missing original provenance: {rel}')
        require(resource_digest(bundle / rel) == record['local_sha256'],
                f'Changed adapted resource: {bundle / rel}')
    require(list(bundle.rglob('SKILL.md')) == [bundle / 'SKILL.md'], 'Nested public skill registered')
    references = ['SKILL.md'] + [p.relative_to(bundle).as_posix()
                               for p in (bundle / 'references').glob('*.md')]
    references += ['grimoire/character/likeness_maximization.md',
                   'grimoire/review/gates_reference.md']
    for rel in references:
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', (bundle / rel).read_text(encoding='utf-8-sig')):
            if '://' not in target and not target.startswith('#'):
                require((bundle / rel).parent.joinpath(target.split('#')[0]).is_file(),
                        f'Broken skill reference: {rel}: {target}')


def smoke(bundle, workspace, run):
    # The installed package stays immutable; upstream caches live in the staged copy.
    task = workspace / 'asset task'
    task.mkdir()
    staged = task / '.img2threejs/toolkit'
    shutil.copytree(bundle, staged)
    original = {p.relative_to(bundle): digest(p) for p in bundle.rglob('*') if p.is_file()}

    def forge(script, *args, expected=0):
        return run([sys.executable, '-B', str(staged / 'forge' / script), *args], task, expected)

    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', 8, 8, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress((b'\x00' + b'\x60\x90\xc0' * 8) * 8)) + chunk(b'IEND', b'')
    (task / 'concept.png').write_bytes(png)
    forge('stage1_intake/probe_image.py', 'concept.png', '--out', 'image-probe.json')
    require((task / 'image-probe.json').is_file(), 'Image probe did not persist evidence')
    prior_files = {p.relative_to(task) for p in task.rglob('*') if p.is_file()}
    forge('stage3_build/bake_projected_texture.py', '--reference-image', 'concept.png',
          '--mesh-id', 'body', '--out', 'projection-descriptor.json')
    descriptor = json.loads((task / 'projection-descriptor.json').read_text(encoding='utf-8'))
    require('descriptor-only' in descriptor['projectedTextureBake']['status'],
            'Projection capability changed: review the documented runtime-bake boundary')
    new_files = {p.relative_to(task) for p in task.rglob('*') if p.is_file()} - prior_files
    require(new_files == {Path('projection-descriptor.json')},
            'Descriptor smoke must distinguish JSON from actual baked image output')
    forge('state.py', 'init', '--reference', 'concept.png', '--profile', 'generic',
          '--spec', 'object-sculpt-spec.json')
    before = (task / '.img2threejs/state.json').read_bytes()
    forge('next.py', '--state', '.img2threejs/state.json', 'object-sculpt-spec.json')
    require((task / '.img2threejs/state.json').read_bytes() == before, 'Resume changed task state')
    forge('stage2_spec/new_pre_spec_assessment.py', 'Stylized tower', '--image', 'concept.png',
          '--complexity', 'simple', '--out', 'assessment.json')
    assessment = json.loads((task / 'assessment.json').read_text(encoding='utf-8'))
    require('localSpecSearch' in assessment, 'Bundled corpus did not supply local spec evidence')
    forge('stage2_spec/new_sculpt_spec.py', 'Stylized tower', '--image', 'concept.png',
          '--assessment', 'assessment.json', '--out', 'object-sculpt-spec.json')
    # An unreviewed starter must not silently become a production factory.
    forge('stage3_build/generate_threejs_factory.py', 'object-sculpt-spec.json',
          '--out', 'model.ts', '--blocked-report', 'blocked.json', expected=2)
    blocked = json.loads((task / 'blocked.json').read_text(encoding='utf-8'))
    require(blocked['gate'] == 'strict-quality' and blocked['status'] == 'BLOCKED'
            and not (task / 'model.ts').exists(), 'Strict generation gate was bypassed')
    # A real minimal GLB container proves the successful handoff-probe path as well.
    positions = struct.pack('<9f', 0, 0, 0, 1, 0, 0, 0, 1, 0)
    document = {'asset': {'version': '2.0'}, 'scene': 0, 'scenes': [{'nodes': [0]}],
                'nodes': [{'name': 'Triangle', 'mesh': 0}],
                'meshes': [{'primitives': [{'attributes': {'POSITION': 0}}]}],
                'buffers': [{'byteLength': len(positions)}],
                'bufferViews': [{'buffer': 0, 'byteLength': len(positions)}],
                'accessors': [{'bufferView': 0, 'componentType': 5126, 'count': 3,
                               'type': 'VEC3', 'min': [0, 0, 0], 'max': [1, 1, 0]}]}
    encoded = json.dumps(document).encode('utf-8')
    encoded += b' ' * (-len(encoded) % 4)
    glb = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(encoded) + 8 + len(positions))
    glb += struct.pack('<II', len(encoded), 0x4E4F534A) + encoded
    glb += struct.pack('<II', len(positions), 0x004E4942) + positions
    (task / 'generated.glb').write_bytes(glb)
    forge('stage1_intake/probe_glb.py', 'generated.glb', '--out', 'glb-probe.json')
    probe = json.loads((task / 'glb-probe.json').read_text(encoding='utf-8'))
    require(probe['scene']['meshCount'] == 1 and probe['referenceReadiness'] == 'pass',
            'Valid GLB could not be inspected')
    require(probe['sha256'] == digest(task / 'generated.glb'), 'GLB evidence hash is stale')
    (task / 'invalid.glb').write_bytes(b'not a glb')
    forge('stage1_intake/probe_glb.py', 'invalid.glb', expected=2)
    after = {p.relative_to(bundle): digest(p) for p in bundle.rglob('*') if p.is_file()}
    require(after == original, 'Execution modified the installed package')

    # Synthetic terminal state: these fixtures do not claim real reconstruction evidence.
    terminal = workspace / 'terminal evidence'
    terminal.mkdir()

    def terminal_forge(script, *args, expected=0):
        return run([sys.executable, '-B', str(staged / 'forge' / script), *args], terminal, expected)

    terminal_forge('state.py', 'init', '--reference', 'synthetic-concept.png')
    state_path = terminal / '.img2threejs/state.json'
    state = json.loads(state_path.read_text(encoding='utf-8'))
    state['currentPass'] = 'complete'
    for row in state['checklist']:
        if row['scope'] in ('setup', 'pass'):
            row.update(status='done', evidence=['synthetic-fixture-only'])
    state_path.write_text(json.dumps(state), encoding='utf-8')
    before = state_path.read_bytes()
    terminal_forge('stage3_build/run_gates.py', '--workspace', '.', expected=1)
    terminal_forge('state.py', 'mark', 'plugin-gates', '--evidence', 'synthetic-fixture-only', expected=2)
    require(state_path.read_bytes() == before, 'Failed/out-of-order terminal work changed state')
    terminal_forge('state.py', 'mark', 'part-coverage', 'action-ready',
                   '--evidence', 'synthetic-fixture-only')
    terminal_forge('stage3_build/emit_target.py', '--spec', 'unused.json', '--workspace', '.')
    state = json.loads(state_path.read_text(encoding='utf-8'))
    require(state['currentStep'] == 'emission-target', 'No-target no-op unexpectedly completed emission')
    (terminal / 'export-report.json').write_text(json.dumps({
        'route': 'project-exporter', 'status': 'pending', 'fixture': True,
    }), encoding='utf-8')
    terminal_forge('state.py', 'mark', 'emission-target', '--status', 'skipped',
                   '--reason', 'Project GLTFExporter selected; actual export tracked in export-report.json',
                   '--evidence', 'export-report.json')
    _, output = terminal_forge('stage3_build/run_gates.py', '--workspace', '.')
    require(json.loads(output) == {}, 'Empty registry unexpectedly supplied plugin gates')
    (terminal / 'plugin-gates.json').write_text(output, encoding='utf-8')
    terminal_forge('state.py', 'mark', 'plugin-gates', '--evidence', 'plugin-gates.json')
    _, output = terminal_forge('state.py', 'status', '--json')
    status = json.loads(output)
    require(status['status'] == 'complete' and not status['pending'],
            'Documented project-exporter closure leaves a mandatory step pending')
    report = json.loads((terminal / 'export-report.json').read_text(encoding='utf-8'))
    require(report['status'] == 'pending' and not list(terminal.glob('*.glb')),
            'Checklist completion must not manufacture exported-asset evidence')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--builder', choices=('powershell', 'sh'), required=True)
    parser.add_argument('--shell')
    parser.add_argument('--keep', action='store_true')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent.parent
    shell = args.shell or shutil.which(args.builder)
    require(shell, f'Missing shell: {args.builder}')
    workspace = Path(tempfile.mkdtemp(prefix='myskills-img2-test-')).resolve()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
               IMG2_HOME=str(workspace / 'empty-plugin-registry'))

    def run(command, cwd, expected=0):
        with tempfile.TemporaryFile() as log:
            result = subprocess.run(command, cwd=cwd, env=env, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=600)
            log.seek(0)
            output = log.read().decode('utf-8', errors='replace')
        if expected is not None:
            require(result.returncode == expected,
                    f'Command failed ({result.returncode}): {command}\n{output[-5000:]}')
        return result.returncode, output

    try:
        root = workspace / 'build'
        root.mkdir()
        for rel in ('scripts', '.codebuddy/references', '.claude/rules'):
            shutil.copytree(repo / rel, root / rel)
        for rel in (f'.codebuddy/skills/{SKILL}', '.codebuddy/skills/cs-minimal',
                    '.codebuddy/agents/cs-cocos-specialist', '.codebuddy/agents/cs-blender-operator'):
            shutil.copytree(repo / rel, root / rel)
        for rel in ('AGENTS.md', 'GEMINI.md', '.codebuddy/AGENTS.md', '.codebuddy/CODEBUDDY.md',
                    '.codebuddy/settings.json', f'.codebuddy/commands/{SKILL}.md',
                    '.codebuddy/agents/cs-frontend-lead.md', '.codebuddy/agents/cs-cocos-specialist.md',
                    '.codebuddy/agents/cs-blender-operator.md'):
            if (repo / rel).exists():
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(repo / rel, root / rel)
        if args.builder == 'sh':
            for script in (root / 'scripts').rglob('*.sh'):
                script.write_bytes(script.read_bytes().replace(b'\r\n', b'\n'))
        # CodeBuddy's installer records source revision; use a disposable local repository.
        run(['git', 'init', '-b', 'fixture'], root)
        run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
             'commit', '--allow-empty', '-m', 'Isolated installer fixture'], root)

        def script(name, *arguments):
            command = [shell]
            if args.builder == 'powershell':
                command += ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File']
            extension = 'ps1' if args.builder == 'powershell' else 'sh'
            return run(command + [f'scripts/{name}.{extension}', *arguments], root)

        script('build-adapters')
        for tree in TREES:
            verify_bundle(root / tree / SKILL)
        ui = (root / '.agents/skills' / SKILL / 'agents/openai.yaml').read_text(encoding='utf-8-sig')
        require('allow_implicit_invocation: false' not in ui, 'Cocos cannot select the skill implicitly')
        print('PASS: five adapter trees contain intact runtime resources and skill metadata.', flush=True)
        # Each platform gets an independent destination/manifest; installations can overlap.
        def install(target):
            destination = workspace / f'installed {target}'
            if args.builder == 'powershell':
                script('install', '-Target', target, '-Destination', str(destination), '-Merge')
            else:
                script('install', '--target', target, '--destination', f'../installed {target}')
            tree = {'codebuddy': '.codebuddy/skills', 'codex': '.agents/skills',
                    'gemini': '.gemini/skills'}[target]
            verify_bundle(destination / tree / SKILL)
            return destination

        with ThreadPoolExecutor(max_workers=3) as pool:
            destinations = dict(zip(('codebuddy', 'codex', 'gemini'),
                                    pool.map(install, ('codebuddy', 'codex', 'gemini'))))
        require((destinations['codex'] / '.codex/agents/cs-cocos-specialist.toml').is_file(),
                'Codex worker was not installed as a native agent')
        require((destinations['gemini'] / '.gemini/commands' / f'{SKILL}.toml').is_file(), 'Missing Gemini command')
        require((destinations['codebuddy'] / '.codebuddy/commands' / f'{SKILL}.md').is_file(), 'Missing CodeBuddy command')
        print('PASS: CodeBuddy, Codex and Gemini project installs include the skill and callers.', flush=True)
        smoke(destinations['codex'] / '.agents/skills' / SKILL, workspace, run)
        print('PASS: installed Forge runs intake, state/resume and corpus/spec creation; invalid generation/GLB fail.', flush=True)
        print('PASS: descriptor-only output and project-exporter state closure are verified; no real bake/export claimed.', flush=True)
    finally:
        if args.keep:
            print(f'Workspace: {workspace}', flush=True)
        else:
            require(workspace.parent == Path(tempfile.gettempdir()).resolve()
                    and workspace.name.startswith('myskills-img2-test-'), 'Unsafe cleanup path')
            shutil.rmtree(workspace)


if __name__ == '__main__':
    main()
