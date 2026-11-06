"""Verify glyph availability in the disposable Linux screenshot environment."""
from pathlib import Path
import re
import subprocess


def font_environment():
    probes = []
    for point in (0x754C, 0x10400, 0x1F600):
        matched = subprocess.check_output(
            ['fc-match', '-f', '%{family}\n%{file}\n%{index}\n', f'sans-serif:charset={point:x}'],
            text=True, timeout=10).splitlines()
        if len(matched) != 3:
            raise RuntimeError('Font lookup did not identify one face')
        family, filename, index = matched
        charset = subprocess.check_output(
            ['fc-query', f'--index={index}', '--format=%{charset}', filename], text=True, timeout=10)
        covered = False
        for token in charset.split():
            if not re.fullmatch(r'[0-9a-f]+(?:-[0-9a-f]+)?', token):
                raise RuntimeError('Unexpected font charset format')
            ends = [int(value, 16) for value in token.split('-')]
            if ends[0] <= point <= ends[-1]:
                covered = True
        if not covered:
            raise RuntimeError(f'Missing test glyph U+{point:04X}; install the documented review fonts')
        probes.append({'codepoint': f'U+{point:04X}', 'available_family': family,
                       'file': Path(filename).name, 'glyph_available': True})
    packages = subprocess.check_output(
        ['dpkg-query', '-W', '-f=${Package} ${Version}\n',
         'fonts-noto-core', 'fonts-noto-cjk', 'fonts-noto-color-emoji'], text=True, timeout=10).splitlines()
    return {'available_faces': probes, 'installed_packages': packages,
            'scope': 'font availability; actual glyph appearance requires screenshot review'}
