"""Approval-checked Docker execution with bounded resources and output."""
import json
import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import threading
import time
from uuid import uuid4

try:
    from .workflow_service import LOCK, folder, read, save, now, verify_approval
except ImportError:
    from workflow_service import LOCK, folder, read, save, now, verify_approval

ROOT = Path(__file__).resolve().parents[1]
CANCEL = {}
RUN_LOCK = threading.Lock()
TEST_TIMEOUT_SECONDS = 90


def command(args, timeout=120, cancel=None, limit=100000):
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    chunks, count = [], [0]
    exceeded = threading.Event()
    def drain():
        while True:
            data = process.stdout.read(4096)
            if not data:
                break
            remaining = max(0, limit - count[0])
            chunks.append(data[:remaining])
            count[0] += len(data)
            if count[0] > limit:
                exceeded.set()
    reader = threading.Thread(target=drain, daemon=True)
    reader.start()
    deadline = time.monotonic() + timeout
    reason = None
    while process.poll() is None:
        if cancel and cancel.is_set():
            reason = 'cancelled'
        elif exceeded.is_set():
            reason = 'output_limit'
        elif time.monotonic() >= deadline:
            reason = 'timeout'
        if reason:
            process.kill()
            break
        time.sleep(0.1)
    process.wait()
    reader.join(timeout=3)
    process.stdout.close()
    if exceeded.is_set() and reason is None:
        reason = 'output_limit'
    return process.returncode, b''.join(chunks).decode('utf-8', errors='replace'), reason


def cancel_run(session_id):
    with LOCK:
        event = CANCEL.get(session_id)
        if event:
            event.set()


def start(session_id):
    with LOCK:
        state = read(session_id)
        if state['status'] != 'approved':
            raise ValueError('Approve tests before starting a run. Each approval can run once.')
        verify_approval(state)
        state.update(status='queued', results=[], error=None)
        state['events'].append({'at': now(), 'action': 'run_requested'})
        save(state)
        CANCEL[session_id] = threading.Event()
    thread = threading.Thread(target=execute, args=(session_id,), daemon=True)
    thread.start()


def execute(session_id):
    tag = 'groupo-qa-run:' + uuid4().hex
    event = CANCEL[session_id]
    try:
        with RUN_LOCK:
            state = read(session_id)
            tests = verify_approval(state)
            if event.is_set():
                raise ValueError('Run cancelled before execution.')
            with LOCK:
                state.update(status='running', started=now())
                save(state)
            rc, output, reason = command(['docker', 'image', 'inspect', 'budgetme-sandbox:local', '--format', '{{.Id}}'], timeout=20)
            if rc or reason:
                raise ValueError('Docker is unavailable or budgetme-sandbox:local is missing. Start Docker Desktop and build the sandbox image first. ' + output[-1000:])
            base_id = output.strip()
            # A private tag pins the local base for this run. No network or dependency installation is used.
            base_tag = 'groupo-qa-base:' + uuid4().hex
            rc, output, reason = command(['docker', 'tag', base_id, base_tag], timeout=20)
            if rc or reason:
                raise ValueError('Could not prepare the local sandbox base.')
            try:
                with TemporaryDirectory(prefix='groupo-build-') as temporary:
                    build = Path(temporary)
                    shutil.copytree(folder(session_id) / 'source', build / 'source')
                    qa = build / 'qa'
                    qa.mkdir()
                    for name in ('runner.py', '_qa_settings.py'):
                        shutil.copyfile(ROOT / 'sandbox' / 'workflow' / name, qa / name)
                    (qa / 'proposals').mkdir()
                    for test in tests:
                        (qa / 'proposals' / ('case_' + test['id'] + '.py')).write_text(test['code'], encoding='utf-8')
                    (build / 'Dockerfile').write_text(
                        f'FROM {base_tag}\nUSER root\nWORKDIR /workspace\n'
                        'COPY source/ /workspace/\nCOPY qa/ /qa/\n'
                        'ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1\nUSER 10001:10001\n', encoding='utf-8')
                    rc, output, reason = command(['docker', 'build', '--network', 'none', '--pull=false', '-t', tag, str(build)], timeout=180, cancel=event)
                    if rc or reason:
                        raise ValueError('Sandbox preparation failed: ' + (reason or output[-1500:]))
                rc, image_id, reason = command(['docker', 'image', 'inspect', tag, '--format', '{{.Id}}'], timeout=20)
                if rc or reason:
                    raise ValueError('Could not identify the prepared image.')
                state.update(image_id=image_id.strip(), base_image_id=base_id)
                with LOCK:
                    save(state)
                for test in tests:
                    if event.is_set():
                        break
                    verify_approval(state)
                    name = 'groupo-qa-' + uuid4().hex
                    started = time.monotonic()
                    args = ['docker', 'run', '--rm', '--name', name, '--network', 'none', '--read-only',
                            '--tmpfs', '/tmp:rw,noexec,nosuid,size=64m', '--memory', '512m', '--memory-swap', '512m',
                            '--cpus', '1', '--pids-limit', '64', '--cap-drop', 'ALL',
                            '--security-opt', 'no-new-privileges', '--user', '10001:10001',
                            image_id.strip(), 'python', '-I', '/qa/runner.py', state['adapter'], 'case_' + test['id']]
                    try:
                        rc, output, reason = command(args, timeout=TEST_TIMEOUT_SECONDS, cancel=event)
                    finally:
                        command(['docker', 'rm', '-f', name], timeout=15)
                    record = {'id': test['id'], 'status': 'error', 'seconds': round(time.monotonic() - started, 2),
                              'output': output[-16000:], 'exit_code': rc, 'detail': '', 'tests_run': 0}
                    if reason:
                        record.update(status=reason, detail='Execution stopped: ' + reason)
                    else:
                        lines = [line.removeprefix('QA_RESULT_JSON=') for line in output.splitlines() if line.startswith('QA_RESULT_JSON=')]
                        try:
                            if len(lines) != 1:
                                raise ValueError()
                            result = json.loads(lines[0])
                            if result['status'] not in {'passed', 'failed', 'error', 'skipped'} or type(result['tests_run']) is not int or not 1 <= result['tests_run'] <= 20:
                                raise ValueError()
                            if rc != (0 if result['status'] in {'passed', 'skipped'} else 1):
                                raise ValueError()
                            record.update(status=result['status'], tests_run=result['tests_run'],
                                          detail='\n'.join(item['detail'] for item in result['records'])[:12000])
                        except (ValueError, KeyError, TypeError):
                            record['detail'] = 'No valid test-group result was returned. Check the execution output.'
                    state['results'].append(record)
                    with LOCK:
                        save(state)
                state['status'] = 'cancelled' if event.is_set() else 'completed'
            finally:
                command(['docker', 'image', 'rm', base_tag], timeout=20)
    except Exception as error:
        state = read(session_id)
        state.update(status='cancelled' if event.is_set() else 'blocked', error=str(error)[:2000])
    finally:
        try:
            command(['docker', 'image', 'rm', tag], timeout=20)
        except OSError:
            pass
        with LOCK:
            state = locals().get('state', read(session_id))
            state['finished'] = now()
            state['events'].append({'at': now(), 'action': 'run_finished', 'status': state['status']})
            save(state)
            CANCEL.pop(session_id, None)
