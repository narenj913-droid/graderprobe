#!/usr/bin/env python3
"""Copy GraderProbe raw trial outputs to a sanitized public directory and hash them."""
from __future__ import annotations
import argparse
import hashlib
import re
import shutil
from pathlib import Path

TEXT_EXTENSIONS = {'.json', '.md', '.html', '.txt', '.log', '.sarif', '.yaml', '.yml', '.py', '.xml'}
SECRET_PATTERN = re.compile(
    r'(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)'
)

def path_variants(value: str) -> set[str]:
    if not value:
        return set()
    variants = {value, value.replace('\\', '/'), value.replace('/', '\\'), value.replace('\\', '\\\\')}
    return {v for v in variants if v}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True, help='Raw local output directory')
    parser.add_argument('--destination', required=True, help='Sanitized public output directory')
    parser.add_argument('--replace', action='append', default=[], metavar='PATH=LABEL', help='Repeat for repo, worktree, home, temp paths')
    args = parser.parse_args()

    source = Path(args.source).resolve()
    destination = Path(args.destination).resolve()
    if not source.is_dir():
        raise SystemExit(f'Source directory does not exist: {source}')
    if destination == source or source in destination.parents:
        raise SystemExit('Destination must not be inside source or be the source itself.')

    replacements = []
    for item in args.replace:
        if '=' not in item:
            raise SystemExit(f'Invalid --replace {item!r}; expected PATH=LABEL')
        old, label = item.split('=', 1)
        if old:
            replacements.extend((variant, label) for variant in path_variants(old))
    replacements.sort(key=lambda pair: len(pair[0]), reverse=True)

    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)

    for path in destination.rglob('*'):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            content = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        for old, label in replacements:
            content = content.replace(old, label)
        content = re.sub(r'(?i)[A-Z]:\\Users\\[^\\"\r\n]+\\AppData\\Local\\Temp', '<TEMP>', content)
        content = re.sub(r'(?i)[A-Z]:/Users/[^/"\r\n]+/AppData/Local/Temp', '<TEMP>', content)
        path.write_text(content, encoding='utf-8', newline='')

    home = Path.home()
    username = home.name
    leftovers = []
    for path in destination.rglob('*'):
        if not path.is_file():
            continue
        content = path.read_text(encoding='utf-8', errors='ignore')
        if username and username.lower() in content.lower():
            leftovers.append(f'username:{path.relative_to(destination)}')
        if SECRET_PATTERN.search(content):
            leftovers.append(f'secret-pattern:{path.relative_to(destination)}')
    if leftovers:
        raise SystemExit('Sanitization scan failed: ' + ', '.join(leftovers[:20]))

    files = sorted(p for p in destination.rglob('*') if p.is_file() and p.name != 'SHA256SUMS.txt')
    manifest = ''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(destination).as_posix()}\n' for p in files)
    (destination / 'SHA256SUMS.txt').write_text(manifest, encoding='utf-8')
    print(f'SANITIZED_OK files={len(files)} manifest={destination / "SHA256SUMS.txt"}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
