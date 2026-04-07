#!/usr/bin/env python3

import subprocess
import sys
import os
import time
import threading
import shutil
from pathlib import Path

ROOT     = Path(__file__).resolve().parent
BACKEND  = ROOT / 'backend'
FRONTEND = ROOT / 'frontend'
ELECTRON = ROOT / 'electron'
VENV     = BACKEND / 'venv'
PYTHON   = VENV / 'bin' / 'python3'
PIP      = VENV / 'bin' / 'pip'

DJANGO_PORT = 8765

RED    = '\033[91m'
GREEN  = '\033[92m'
YELLOW = '\033[93m'
CYAN   = '\033[96m'
RESET  = '\033[0m'
BOLD   = '\033[1m'

processes: list[subprocess.Popen[str]] = []
stopping = threading.Event()


def log(prefix, color, line):
    print(f"{color}{BOLD}[{prefix}]{RESET} {line}", flush=True)


def stream(proc, prefix, color):
    for line in iter(proc.stdout.readline, ''):
        if stopping.is_set():
            break
        log(prefix, color, line.rstrip())


def run(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, check=True)


def setup_venv():
    reqs = BACKEND / 'requirements.txt'

    if not VENV.exists():
        log('setup', GREEN, 'Creating virtual environment...')
        run([sys.executable, '-m', 'venv', str(VENV)])
        run([str(PIP), 'install', '--upgrade', 'pip', '-q'])
        run([str(PIP), 'install', '--ignore-installed', '-r', str(reqs)])
    else:
        result = subprocess.run(
            [str(PIP), 'show', 'python-decouple'],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            log('setup', GREEN, 'Repairing virtual environment...')
            run([str(PIP), 'install', '--ignore-installed', '-r', str(reqs)])
        else:
            log('setup', GREEN, 'Virtual environment OK.')


def migrate():
    log('setup', GREEN, 'Running migrations...')
    env = {**os.environ, 'DJANGO_SETTINGS_MODULE': 'firecat_project.settings'}
    run([str(PYTHON), 'manage.py', 'migrate', '--run-syncdb'], cwd=BACKEND, env=env)


def check_node():
    if not shutil.which('node'):
        log('setup', RED, 'Node.js not found. Install from https://nodejs.org')
        sys.exit(1)


def npm_install(cwd, label):
    node_modules = cwd / 'node_modules'
    if not node_modules.exists():
        log('setup', GREEN, f'Installing {label} dependencies...')
        run(['npm', 'install', '--silent'], cwd=cwd)


def build_frontend():
    dist = FRONTEND / 'dist'
    if not dist.exists():
        log('setup', GREEN, 'Building frontend...')
        run(['npm', 'run', 'build'], cwd=FRONTEND)


def start_django():
    env = {
        **os.environ,
        'DJANGO_SETTINGS_MODULE': 'firecat_project.settings',
        'PYTHONUNBUFFERED': '1',
        'PYTHONPATH': str(BACKEND),
    }
    proc = subprocess.Popen(
        [str(PYTHON), 'manage.py', 'runserver', f'127.0.0.1:{DJANGO_PORT}', '--noreload'],
        cwd=BACKEND, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    processes.append(proc)
    threading.Thread(target=stream, args=(proc, 'django', '\033[94m'), daemon=True).start()
    return proc


def start_vite():
    proc = subprocess.Popen(
        ['npm', 'run', 'dev'],
        cwd=FRONTEND,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    processes.append(proc)
    threading.Thread(target=stream, args=(proc, 'vite', CYAN), daemon=True).start()
    return proc


def wait_for_django():
    import urllib.request
    log('setup', GREEN, f'Waiting for Django on port {DJANGO_PORT}...')
    for _ in range(120):
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{DJANGO_PORT}/api/bookmarks/', timeout=1)
            log('setup', GREEN, 'Django is ready.')
            return True
        except Exception:
            time.sleep(0.5)
    log('setup', RED, 'Django did not start in time.')
    return False


def electron_watcher():
    launcher = ROOT / 'launch_electron.py'
    proc = subprocess.Popen(
        [sys.executable, str(launcher)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    threading.Thread(target=stream, args=(proc, 'electron', YELLOW), daemon=True).start()
    proc.wait()


def kill_all():
    stopping.set()
    for proc in processes:
        try:
            proc.terminate()
        except Exception:
            pass
    time.sleep(1)
    for proc in processes:
        try:
            if proc.poll() is None:
                proc.kill()
        except Exception:
            pass


def main():
    print(f"\n{BOLD}{GREEN}🔥 Firecat Dev Launcher{RESET}\n")

    try:
        setup_venv()
        migrate()
        check_node()
        npm_install(FRONTEND, 'frontend')
        npm_install(ELECTRON, 'electron')
        build_frontend()

        print()
        log('setup', GREEN, 'Starting services...\n')

        start_django()

        if not wait_for_django():
            kill_all()
            sys.exit(1)

        start_vite()
        time.sleep(1)

        t = threading.Thread(target=electron_watcher, daemon=True)
        t.start()
        time.sleep(2)

        log('setup', GREEN, 'All services running. Press Ctrl+C to stop.\n')

        while not stopping.is_set():
            time.sleep(1)
            dead = [p for p in processes if p.poll() is not None]
            if dead:
                log('setup', RED, 'Django or Vite exited unexpectedly. Shutting down...')
                break

    except KeyboardInterrupt:
        print(f"\n{YELLOW}Stopping...{RESET}")
    finally:
        kill_all()
        print(f"{GREEN}Done.{RESET}\n")


if __name__ == '__main__':
    main()