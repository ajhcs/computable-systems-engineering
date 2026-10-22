#!/usr/bin/env python3
"""Optional browser preview. No browser installation or dependency changes."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path, help='existing gallery build output')
    parser.add_argument('--browser', required=True, type=Path, help='installed Chromium executable')
    parser.add_argument('--library-path', help='existing shared-library directory, if required')
    args = parser.parse_args()
    output = args.output.resolve()
    svg, png = output / 'overview.svg', output / 'overview.png'
    env = os.environ.copy()
    if args.library_path:
        env['LD_LIBRARY_PATH'] = args.library_path
    command = [str(args.browser), '--headless', '--no-sandbox', '--disable-gpu', '--allow-file-access-from-files', '--force-device-scale-factor=1', '--window-size=1200,420', '--screenshot=' + str(png), svg.as_uri()]
    result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=60)
    if result.returncode or not png.is_file():
        raise SystemExit('Browser preview failed: ' + result.stderr[-600:])
    receipt = {'claim': 'actual installed browser rasterization only; independent visual acceptance remains separate', 'browser': str(args.browser), 'browser_sha256': digest(args.browser), 'library_path': args.library_path, 'viewport': [1200, 420], 'svg_sha256': digest(svg), 'png_sha256': digest(png), 'command_template': 'BROWSER --headless --no-sandbox --disable-gpu --allow-file-access-from-files --force-device-scale-factor=1 --window-size=1200,420 --screenshot=OUTPUT/overview.png file:///OUTPUT/overview.svg'}
    (output / 'preview-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    path = output / 'build-manifest.json'
    manifest = json.loads(path.read_text())
    for name in ('overview.png', 'preview-receipt.json'):
        manifest['files'][name] = digest(output / name)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    print('Rendered overview.png; source/image bindings added to the build manifest')


if __name__ == '__main__':
    main()
