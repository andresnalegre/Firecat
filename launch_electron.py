#!/usr/bin/env python3
import urllib.request
import subprocess
import sys
import time
from pathlib import Path

ELECTRON    = Path(__file__).resolve().parent / 'electron'
DJANGO_PORT = 8765

def wait_for_django():
    for _ in range(120):
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{DJANGO_PORT}/api/bookmarks/', timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
    return False

def main():
    if not wait_for_django():
        print('[launch_electron] Django not ready, aborting.', flush=True)
        sys.exit(1)

    electron_bin = ELECTRON / 'node_modules' / '.bin' / 'electron'
    import os
    env = {**os.environ, 'FIRECAT_EXTERNAL_DJANGO': '1'}

    while True:
        proc = subprocess.run(
            [str(electron_bin), '--name=Firecat', '.'],
            cwd=ELECTRON,
            env=env,
        )
        print(f'[launch_electron] Electron exited ({proc.returncode}). Relaunching...', flush=True)
        time.sleep(1)

if __name__ == '__main__':
    main()