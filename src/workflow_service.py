"""Local PDF-to-report sessions. Generated Python is never executed by this process."""

try:
    from .console_logging import trace_operation, log_event, log_error
except ImportError:
    from console_logging import trace_operation, log_event, log_error

import ast
from datetime import datetime, timezone, timedelta
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import shutil
import threading
from uuid import uuid4

from jsonschema import validate
from pypdf import PdfReader

try:
    from .model_service import complete, load_prompt
    from .requirement_extraction import extract_requirements, VERSION as REQUIREMENTS_VERSION
except ImportError:
    from model_service import complete, load_prompt
    from requirement_extraction import extract_requirements, VERSION as REQUIREMENTS_VERSION

LOCK = threading.RLock()
CODE_WORKER_OWNER = uuid4().hex
EXCLUDED = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', 'uploads', 'media',
            'staticfiles', 'dist', 'build', '.aws', '.ssh', '.codex', '.agents'}
EXTENSIONS = {'.py', '.html', '.css', '.js', '.ts', '.tsx', '.jsx', '.vue', '.sql'}
SCHEMA = {
    'type': 'object', 'additionalProperties': False, 'required': ['tests'],
    'properties': {'tests': {'type': 'array', 'minItems': 1, 'maxItems': 3, 'items': {
        'type': 'object', 'additionalProperties': False,
        'required': ['title', 'requirement', 'expected', 'limitations', 'code'],
        'properties': {key: {'type': 'string', 'minLength': 1, 'maxLength': size}
                       for key, size in [('title', 200), ('requirement', 300), ('expected', 1500),
                                         ('limitations', 1500), ('code', 14000)]}
    }}}
}



def uganda_time(value, fmt='%Y-%m-%d %H:%M:%S'):
    """Convert recorded ISO timestamps to Uganda's EAT (UTC+03:00)."""
    if not value:
        return 'Not recorded'
    try:
        stamp = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if stamp.tzinfo is None:
            return str(value)  # Do not invent a timezone for legacy naive records.
        return stamp.astimezone(timezone(timedelta(hours=3), 'EAT')).strftime(fmt)
    except ValueError:
        return str(value)


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def home():
    root = Path(os.environ.get('QA_WORKFLOW_HOME', str(Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'GroupOQA' / 'sessions')))
    if root.resolve().is_relative_to(Path(__file__).resolve().parents[1]):
        raise ValueError('QA_WORKFLOW_HOME must be outside the submission repository.')
    root.mkdir(parents=True, exist_ok=True)
    return root


def folder(session_id):
    if not re.fullmatch(r'[a-f0-9]{32}', session_id):
        raise ValueError('Invalid session.')
    return home() / session_id


def save(state):
    path = folder(state['id']) / 'session.json'
    temporary = path.with_suffix('.new')
    temporary.write_text(json.dumps(state, indent=2), encoding='utf-8')
    temporary.replace(path)


def read(session_id):
    with LOCK:
        state = json.loads((folder(session_id) / 'session.json').read_text(encoding='utf-8'))
        if state.get('requirements_version') != REQUIREMENTS_VERSION:
            state['requirements'] = extract_requirements(state['pages'])
            state['requirements_version'] = REQUIREMENTS_VERSION
            save(state)
        changed = False
        if state['status'] == 'code_generating' and state.get('code_generation_owner') != CODE_WORKER_OWNER:
            # A daemon worker cannot survive a process restart. Preserve descriptions
            # and existing execution approvals; require an explicit retry.
            for test in state['tests']:
                if test.get('review_status') == 'approved' and test.get('code_status') in {'queued', 'generating'}:
                    test.update(code_status='failed', code_error='Code generation was interrupted when the application stopped. Retry code generation.')
            state.update(status='approved' if state.get('approval') else 'review',
                         error='Code generation was interrupted. Retry the affected approved cases.')
            state.pop('code_generation_owner', None)
            changed = True
        for test in state['tests']:
            if test.get('review_status') == 'approved' and not test.get('code') and test.get('code_status') not in {'queued', 'generating', 'failed', 'waiting'}:
                test.update(code_status='failed', code_error='No generated code is available. Retry code generation.')
                changed = True
        recorded = {}
        if state.get('error') and ('Code generation failed' in state['error'] or 'Approval saved.' in state['error']):
            for event in state.get('events', []):
                if event['action'] == 'test_descriptions_approved' and event['at'] >= state.get('generated', ''):
                    recorded.update({test_id: event['at'] for test_id in event.get('test_ids', [])})
        for test in state['tests']:
            if test['id'] in (state.get('approval') or {}).get('tests', {}) and test.get('code'):
                if test.get('review_status') != 'approved' or test.get('code_status') != 'ready':
                    test.update(review_status='approved', code_status='ready')
                    changed = True
            elif test['id'] in recorded and test.get('review_status') != 'approved':
                test.update(review_status='approved', approved_at=recorded[test['id']], code_status='failed', code_error=state['error'])
                changed = True
        if changed:
            save(state)
        if (state.get('error') or '').startswith('Code generation failed.'):
            reason = state['error'].split('retry. ', 1)[-1] if 'retry. ' in state['error'] else state['error'].removeprefix('Code generation failed.').strip()
            state['error'] = 'Approval saved. Code generation failed: ' + reason
            for test in state['tests']:
                if test.get('code_status') == 'failed':
                    test['code_error'] = reason
            save(state)
        return state


def recent():
    items = []
    for path in home().glob('*/session.json'):
        try:
            state = json.loads(path.read_text(encoding='utf-8'))
            items.append({key: state[key] for key in ('id', 'name', 'created', 'status')})
        except (ValueError, KeyError, OSError):
            continue
    return sorted(items, key=lambda item: item['created'], reverse=True)[:20]


def snapshot(source, destination):
    source = source.expanduser().resolve(strict=True)
    if not source.is_dir() or source == Path(source.anchor) or source == Path.home():
        raise ValueError('Choose the application folder, not your home folder or a drive.')
    manifest = {}
    total = 0
    for directory, dirs, files in os.walk(source, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED and not d.startswith('.')
                         and not (Path(directory) / d).is_symlink()
                         and not (Path(directory) / d).is_junction())
        for name in sorted(files):
            path = Path(directory) / name
            if (path.is_symlink() or path.suffix.lower() not in EXTENSIONS or name.startswith('.')
                    or name in {'settings.py', 'local_settings.py', 'conftest.py'}
                    or any(word in name.lower() for word in ('secret', 'credential', 'private_key'))):
                continue
            if not path.resolve().is_relative_to(source):
                continue
            data = path.read_bytes()
            if len(data) > 2_000_000:
                continue
            total += len(data)
            if total > 40_000_000 or len(manifest) >= 2000:
                raise ValueError('This prototype supports up to 2,000 source files and 40 MB. Choose a smaller application folder.')
            relative = path.relative_to(source).as_posix()
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            manifest[relative] = digest(data)
    if not manifest:
        raise ValueError('No supported source files were found in that folder.')
    return manifest


@trace_operation("AGENT", "Create project snapshot")
def create(pdf, filename, code_path, adapter, focus, manual_text="", allow_empty=False):
    if adapter not in {'budgetme', 'python'}:
        raise ValueError('Select a supported test environment.')
    if allow_empty and not pdf and not manual_text.strip():
        pages, filename = [], 'No requirements'
    elif manual_text.strip():
        text = manual_text.strip()
        if not 30 <= len(text) <= 100000:
            raise ValueError('Enter between 30 and 100,000 characters of requirements.')
        pages = [{'page': 1, 'text': text}]
        filename = 'Manual requirements'
    else:
        if len(pdf) > 10_000_000 or not pdf.startswith(b'%PDF-'):
            raise ValueError('Upload a PDF smaller than 10 MB.')
        try:
            reader = PdfReader(BytesIO(pdf))
            if reader.is_encrypted or len(reader.pages) > 150:
                raise ValueError('Use an unencrypted PDF with no more than 150 pages.')
            pages = [{'page': i + 1, 'text': (page.extract_text() or '')} for i, page in enumerate(reader.pages)]
        except ValueError:
            raise
        except Exception as error:
            raise ValueError('The PDF could not be read. Export it again and retry.') from error
        if sum(len(page['text'].strip()) for page in pages) < 30:
            raise ValueError('This PDF has no readable text. Export a text-based PDF; scanned PDFs need OCR first.')
        if sum(len(page['text']) for page in pages) > 1_000_000:
            raise ValueError('The extracted PDF text is too large. Upload a smaller requirements document.')
    session_id = uuid4().hex
    root = folder(session_id)
    root.mkdir()
    try:
        manifest = snapshot(Path(code_path), root / 'source')
        if adapter == 'budgetme' and not all(name in manifest for name in ('budgetbuddy/models.py', 'BudgetMe/urls.py')):
            raise ValueError('The BudgetMe environment needs the folder containing manage.py and budgetbuddy.')
        if pdf and not manual_text.strip():
            (root / 'requirements.pdf').write_bytes(pdf)
        try:
            from .rag_service import repository_binding
        except ImportError:
            from rag_service import repository_binding
        state = {'id': session_id, 'name': Path(code_path).name, 'pdf_name': Path(filename).name,
                 'pdf_hash': digest(manual_text.strip().encode() if manual_text.strip() else pdf), 'pages': pages, 'manifest': manifest,
                 'requirements': extract_requirements(pages), 'requirements_version': REQUIREMENTS_VERSION,
                 'snapshot_hash': digest(json.dumps(manifest, sort_keys=True).encode()),
                 'created': now(), 'status': 'ready', 'adapter': adapter, 'focus': focus[:2000],
                 'source_path': str(Path(code_path).expanduser().resolve()),
                 'knowledge_repository': repository_binding(Path(code_path).expanduser().resolve()),
                 'project_key': digest(str(Path(code_path).expanduser().resolve()).casefold().encode()),
                 'tests': [], 'approval': None, 'results': [], 'events': [], 'error': None}
        save(state)
        return state
    except Exception:
        shutil.rmtree(root)
        raise


@trace_operation("RAG", "Assemble project context")
def context(state, requirement_ids=None):
    requirements = state.get('requirements') or extract_requirements(state['pages'])
    if not requirements:
        raise ValueError('No requirement statements could be extracted. Use a PDF with requirement IDs, acceptance criteria, or clear shall/must statements.')
    if requirement_ids is not None:
        requirements = [r for r in requirements if r['id'] in requirement_ids]
        if not requirements:
            raise ValueError('Requirement not found.')
    code_names = ' '.join(state['manifest']).lower()
    def relevance(item):
        terms = set(re.findall(r'[a-z]{4,}', item['title'] + ' ' + item['text']))
        return sum(term.lower() in code_names for term in terms)
    ordered = sorted(requirements, key=lambda item: -relevance(item))
    words = set(re.findall(r'[a-z]{4,}', ' '.join(r['title'] + ' ' + r['text'] for r in ordered[:2]).lower()))
    excerpts, remaining = [], 2400
    for requirement in ordered:
        if remaining <= 0:
            break
        text = (requirement['title'] + '\n' + requirement['text'] + '\n' + '\n'.join(c['id'] + ': ' + c['text'] for c in requirement['criteria']))[:remaining]
        if text.strip():
            excerpts.append({'id': requirement['id'], 'page': requirement['page'], 'status': requirement['status'], 'text': text})
            remaining -= len(text)
    def score(name):
        return (sum(w in name.lower() for w in words) * 10
                + (5 if 'validation' in name else 0) + (3 if name.endswith(('models.py', 'forms.py')) else 0))
    paths = sorted(state['manifest'], key=lambda name: (-score(name), name))
    files, remaining = [], 3500
    for name in paths:
        if remaining <= 0 or len(files) >= 6:
            break
        if not name.endswith('.py'):
            continue
        text = (folder(state['id']) / 'source' / name).read_text(encoding='utf-8', errors='replace')
        if not text.strip():
            continue
        selected = text[:min(remaining, 2200)]
        files.append({'path': name, 'text': selected, 'truncated': len(selected) < len(text)})
        remaining -= len(selected)
    evidence = {'environment': state['adapter'], 'requirements': excerpts,
                'source_files': files, 'file_index': paths[:20],
                'scope_note': 'Small selected excerpts only. Do not claim full SRS or application coverage.'}
    # Bound the actual serialized payload too: escaping and long paths add overhead.
    while len(json.dumps(evidence, ensure_ascii=True)) > 8000:
        if evidence['file_index']:
            evidence['file_index'].pop()
            continue
        largest = max(excerpts + files, key=lambda item: len(item['text']))
        if len(largest['text']) < 64:
            (files if largest in files else excerpts).remove(largest)
            continue
        largest['text'] = largest['text'][:len(largest['text']) // 2]
        largest['truncated'] = True
    return evidence


@trace_operation("CODE", "Validate generated code")
def validate_code(code):
    code = code.strip()
    if code.startswith('```') and code.endswith('```'):
        code = '\n'.join(code.splitlines()[1:-1])
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        raise ValueError('A proposed test has invalid Python syntax. Regenerate the suggestions.') from error
    functions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test_')]
    for node in functions:
        if (isinstance(node, ast.AsyncFunctionDef) or node.decorator_list or node.args.args
                or node.args.posonlyargs or node.args.kwonlyargs or node.args.vararg or node.args.kwarg):
            raise ValueError('Standalone tests must be synchronous and take no fixture arguments. Use unittest or Django TestCase for setup.')
    if functions:
        # Simple assert-based functions can use unittest without executing any code here.
        if any(isinstance(n, ast.Name) and n.id == '_qa_unittest_adapter' for n in ast.walk(tree)):
            raise ValueError('Reserved test adapter name is already used.')
        for node in functions:
            tree.body.remove(node)
            node.args.args.insert(0, ast.arg(arg='self'))
        tree.body.append(ast.Import(names=[ast.alias(name='unittest', asname='_qa_unittest_adapter')]))
        tree.body.append(ast.ClassDef(name='GeneratedFunctionTests', bases=[ast.Attribute(value=ast.Name(id='_qa_unittest_adapter', ctx=ast.Load()), attr='TestCase', ctx=ast.Load())], keywords=[], body=functions, decorator_list=[]))
        code = ast.unparse(ast.fix_missing_locations(tree))
    methods = [method for cls in tree.body if isinstance(cls, ast.ClassDef)
               for method in cls.body if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)) and method.name.startswith('test_')]
    if not methods or len(methods) > 20 or any(isinstance(method, ast.AsyncFunctionDef) for method in methods):
        raise ValueError('No supported runnable tests found. Use 1â€“20 synchronous test_ methods in unittest or Django TestCase classes, or simple test_ functions without fixtures.')
    return code


@trace_operation("AGENT", "Generate test proposals")
def generate(session_id, proposals_only=False):
    with LOCK:
        state = read(session_id)
        if state['status'] not in {'ready', 'review', 'generation_failed', 'generation_queued'}:
            raise ValueError('Start a new session to generate another version after approval or execution.')
        state.update(status='generating', error=None)
        save(state)
    try:
        evidence = context(state)
        schema = json.loads(json.dumps(SCHEMA))
        if proposals_only:
            item = schema['properties']['tests']['items']
            item['required'].remove('code')
            del item['properties']['code']
        response = complete(load_prompt('workflow-proposals.txt' if proposals_only else 'workflow-tests.txt'), json.dumps(evidence),
                            temperature=0.2, max_tokens=2200, schema=schema)
        record_model_trace(state, 'workflow-proposals.txt' if proposals_only else 'workflow-tests.txt', evidence, response)
        payload = json.loads(response['text'])
        validate(payload, schema)
        accepted, warnings = [], []
        for test in payload['tests']:
            try:
                if not proposals_only:
                    test['code'] = validate_code(test['code'])
            except ValueError as error:
                warnings.append(test['title'] + ': ' + str(error))
                continue
            index = len(accepted) + 1
            test.update(id=f'T{index:02}')
            if not proposals_only:
                test['hash'] = digest(test['code'].encode())
            accepted.append(test)
        if not accepted:
            raise ValueError('No runnable proposals were returned. ' + ' '.join(warnings))
        with LOCK:
            if state['tests']:
                state.setdefault('test_history', []).append({'at': now(), 'reason': 'regenerated', 'tests': state['tests']})
            state.update(tests=accepted, generation_warnings=warnings, status='review', model=response['model'],
                         generated=now(), evidence=evidence, approval=None)
            state['events'].append({'at': now(), 'action': 'generated', 'count': len(state['tests'])})
            save(state)
    except Exception as error:
        log_error("CODE", "Generation failed", error)
        with LOCK:
            state.update(status='generation_failed', error='Suggestions could not be generated: ' + str(error)[:500])
            save(state)


@trace_operation("APPROVAL", "Approve executable tests")
def approve(session_id, selected):
    with LOCK:
        state = read(session_id)
        if state['status'] != 'review':
            raise ValueError('Only proposals awaiting review can be approved.')
        ids = set(selected)
        if not ids or not ids.issubset({test['id'] for test in state['tests']}):
            raise ValueError('Select at least one proposed test.')
        if any(t.get('review_status') == 'rejected' for t in state['tests'] if t['id'] in ids):
            raise ValueError('Rejected cases cannot be approved.')
        state['approval'] = {'at': now(), 'reviewer': 'Local operator', 'snapshot_hash': state['snapshot_hash'],
                             'tests': {test['id']: test['hash'] for test in state['tests'] if test['id'] in ids}}
        state['status'] = 'approved'
        state['events'].append({'at': now(), 'action': 'approved', 'test_ids': sorted(ids)})
        save(state)


@trace_operation("APPROVAL", "Verify execution approval")
def verify_approval(state):
    approval = state.get('approval')
    if not approval or approval['snapshot_hash'] != state['snapshot_hash']:
        raise ValueError('A valid approval is required before execution.')
    source = folder(state['id']) / 'source'
    actual = {path.relative_to(source).as_posix(): digest(path.read_bytes()) for path in source.rglob('*') if path.is_file()}
    if actual != state['manifest'] or digest(json.dumps(actual, sort_keys=True).encode()) != state['snapshot_hash']:
        raise ValueError('The saved source snapshot changed. Create a new session and review again.')
    selected = [test for test in state['tests'] if test['id'] in approval['tests']]
    if not selected or len(selected) != len(approval['tests']):
        raise ValueError('Approved tests are missing.')
    for test in selected:
        if digest(test['code'].encode()) != approval['tests'][test['id']]:
            raise ValueError('Approved test code changed. Create a new session and review again.')
    return selected


@trace_operation("APPROVAL", "Approve test descriptions or retry code")
def prepare_approval(session_id, selected, retry=False):
    with LOCK:
        state = read(session_id)
        ids = set(selected)
        eligible = {t['id'] for t in state['tests'] if
                    (t.get('review_status') == 'approved' and t.get('code_status') in {'failed', 'waiting'} if retry
                     else t.get('review_status') not in {'approved', 'rejected'})}
        terminal_retry = retry and state['status'] in {'completed', 'blocked', 'cancelled'}
        ready = set() if terminal_retry else set((state.get('approval') or {}).get('tests', {}))
        if state['status'] not in ({'review', 'approved', 'completed', 'blocked', 'cancelled'} if retry else {'review', 'approved'}) or not ids or not ids.issubset(eligible) or ids & ready:
            raise ValueError('Select cases awaiting approval.' if not retry else 'Select approved cases whose code needs retrying.')
        if ready:
            verify_approval(state)
        if terminal_retry:
            state.setdefault('execution_history', []).append({key: state.get(key) for key in
                ('started', 'finished', 'status', 'results', 'approval', 'image_id', 'base_image_id', 'error')})
            state.update(approval=None, results=[])
            for key in ('started', 'finished', 'image_id', 'base_image_id'):
                state.pop(key, None)
        at = now()
        for test in state['tests']:
            if test['id'] in ids:
                test.update(review_status='approved', code_status='queued', code_error=None)
                test.setdefault('approved_at', at)
        state.update(status='code_generating', error=None, selected_for_code=sorted(ids), code_generation_owner=CODE_WORKER_OWNER,
                     prior_approval=state.get('approval'))
        state['events'].append({'at': at, 'action': 'code_retry_requested' if retry else 'test_descriptions_approved', 'test_ids': sorted(ids)})
        save(state)


@trace_operation("CODE", "Generate approved code")
def generate_approved_code(session_id):
    state = read(session_id)
    if state['status'] != 'code_generating':
        return
    failed = None
    for test in state['tests']:
        if test['id'] not in state['selected_for_code']:
            continue
        if failed:
            test.update(code_status='waiting', code_error='Paused after a code-generation error. Retry explicitly.')
            continue
        try:
            test['code_status'] = 'generating'
            with LOCK:
                save(state)
            if test.get('code'):
                test['hash'] = digest(test['code'].encode())
            else:
                rid = requirement_for_case(state, test)
                evidence = context(state, [rid] if rid else None)
                response = complete(load_prompt('workflow-tests.txt') + '\nThe supplied test description is already approved. Generate its code only; preserve its expected behaviour. Do not claim execution.', json.dumps({
                    'evidence': evidence, 'approved_test': test,
                    'instruction': 'Generate exactly one module implementing this approved test.'
                }), temperature=0.2, max_tokens=2200, schema=SCHEMA)
                record_model_trace(state, 'workflow-tests.txt', evidence, response)
                payload = json.loads(response['text'])
                validate(payload, SCHEMA)
                if len(payload['tests']) != 1:
                    raise ValueError('Expected one code module for the approved test.')
                test['code'] = validate_code(payload['tests'][0]['code'])
                test['hash'] = digest(test['code'].encode())
                test['code_model'] = response['model']
                test['code_generated'] = now()
            log_event('CODE', 'Approved test code ready')
            test.update(code_status='ready', code_error=None)
            state['events'].append({'at': now(), 'action': 'code_validation_passed', 'test_id': test['id'], 'sha256': test['hash']})
        except Exception as error:
            log_error("CODE", "Code generation or validation failed", error)
            failed = str(error)[:500]
            test.pop('code', None)
            test.pop('hash', None)
            test.update(code_status='failed', code_error=failed)
            state['events'].append({'at': now(), 'action': 'code_generation_or_validation_failed', 'test_id': test['id'], 'error': failed})
        with LOCK:
            save(state)
    with LOCK:
        prior = state.get('prior_approval')
        hashes = dict((prior or {}).get('tests', {}))
        for test in state['tests']:
            if test['id'] in state['selected_for_code'] and test.get('code_status') == 'ready':
                hashes[test['id']] = test['hash']
        state['approval'] = prior if failed and hashes == (prior or {}).get('tests', {}) else ({'at': now(), 'reviewer': 'Local operator', 'snapshot_hash': state['snapshot_hash'], 'tests': hashes} if hashes else None)
        state.update(status='approved' if hashes else 'review', error=('Approval saved. Code generation failed: ' + failed) if failed else None)
        state.pop('code_generation_owner', None)
        state['events'].append({'at': now(), 'action': 'code_generation_failed' if failed else 'approved_code_generated', 'test_ids': state['selected_for_code']})
        save(state)


def requirement_for_case(state, test):
    for requirement in state['requirements']:
        if re.search(r'(?<![A-Za-z0-9_-])' + re.escape(requirement['id']) + r'(?:-AC[0-9]+)?(?![A-Za-z0-9_-])', test['requirement'], re.I):
            return requirement['id']
    return None


def pending_requirements(state):
    covered = {requirement_for_case(state, test) for test in state['tests']}
    return [r['id'] for r in state['requirements'] if r['id'] not in covered]


@trace_operation("AGENT", "Queue requirement batch")
def prepare_requirement_batch(session_id, requested=None):
    with LOCK:
        state = read(session_id)
        if state['status'] not in {'ready', 'review', 'approved', 'generation_failed', 'completed', 'blocked', 'cancelled'}:
            raise ValueError('Wait for the current operation to finish.')
        pending = pending_requirements(state)
        if requested and not set(requested).issubset(set(pending)):
            raise ValueError('Choose requirements that do not have cases yet.')
        failures = state.get('requirement_generation_errors', {})
        selected = list(requested) if requested else [r for r in pending if r not in failures] or pending
        if not selected:
            raise ValueError('All requirements already have cases.')
        if state['status'] in {'completed', 'blocked', 'cancelled'}:
            # Consume the old approval: a new cycle must not rerun previously executed tests.
            state.setdefault('execution_history', []).append({key: state.get(key) for key in
                ('started', 'finished', 'status', 'results', 'approval', 'image_id', 'base_image_id', 'error')})
            state['approval'] = None
            state['events'].append({'at': now(), 'action': 'generation_cycle_started', 'requirement_ids': selected[:3]})
        state.update(status='generation_queued', error=None, requirement_batch=selected[:3],
                     generation_completed=0, generation_total=min(3, len(selected)))
        save(state)


@trace_operation("AGENT", "Generate requirement test cases")
def generate_requirement_batch(session_id):
    with LOCK:
        state = read(session_id)
        if state['status'] != 'generation_queued' or not state.get('requirement_batch'):
            return
        state['status'] = 'generating'
        save(state)
    failed = None
    for rid in state['requirement_batch']:
        try:
            evidence = context(state, [rid])
            schema = json.loads(json.dumps(SCHEMA))
            item = schema['properties']['tests']['items']
            item['required'].remove('code')
            del item['properties']['code']
            item['properties']['requirement']['enum'] = [rid]
            response = complete(load_prompt('workflow-requirement-cases.txt'), json.dumps(evidence),
                                temperature=0.2, max_tokens=1600, schema=schema)
            record_model_trace(state, 'workflow-requirement-cases.txt', evidence, response)
            payload = json.loads(response['text'])
            validate(payload, schema)
            next_id = max([int(t['id'][1:]) for t in state['tests'] if re.fullmatch(r'T[0-9]+', t['id'])] or [0]) + 1
            for test in payload['tests']:
                test.update(id=f'T{next_id:02}', review_status='pending', code_status='not_generated')
                state['tests'].append(test)
                next_id += 1
            state.setdefault('requirement_generation_errors', {}).pop(rid, None)
            state['generation_completed'] += 1
            state['model'] = response['model']
            state['generated'] = now()
            log_event('AGENT', 'Requirement test cases generated', count=len(payload['tests']))
            state['events'].append({'at': now(), 'action': 'requirement_cases_generated', 'requirement_id': rid, 'count': len(payload['tests'])})
            with LOCK:
                save(state)
        except Exception as error:
            log_error("CODE", "Code generation or validation failed", error)
            failed = str(error)[:500]
            state.setdefault('requirement_generation_errors', {})[rid] = failed
            break
    with LOCK:
        state.update(status='approved' if state.get('approval') else 'review' if state['tests'] else 'generation_failed',
                     error=('Case generation paused: ' + failed) if failed else None)
        save(state)


def connect(code_path, adapter, name=''):
    state = create(b'', '', code_path, adapter, '', allow_empty=True)
    if name.strip():
        state['name'] = name.strip()[:100]
    state['events'].append({'at': now(), 'action': 'project_connected'})
    save(state)
    return state


@trace_operation("RAG", "Import requirements")
def add_requirements(session_id, *, identifier='', title='', text='', pdf=b'', filename=''):
    """Append new IDs without changing existing cases, approvals or execution evidence."""
    with LOCK:
        state = read(session_id)
        if state['status'] in {'generation_queued', 'generating', 'code_generating', 'queued', 'running'}:
            raise ValueError('Wait for the current operation to finish before adding requirements.')
        if pdf:
            if len(pdf) > 10000000 or not pdf.startswith(b'%PDF-'):
                raise ValueError('Upload a text-based PDF up to 10 MB.')
            try:
                reader = PdfReader(BytesIO(pdf))
                if reader.is_encrypted or len(reader.pages) > 150:
                    raise ValueError('Use an unencrypted PDF with up to 150 pages.')
                pages = [{'page': i + 1, 'text': page.extract_text() or ''} for i, page in enumerate(reader.pages)]
            except Exception as error:
                raise ValueError('The PDF could not be read.') from error
            if sum(len(p['text']) for p in pages) > 1000000:
                raise ValueError('The extracted text exceeds the document limit.')
            records = extract_requirements(pages)
            if not records:
                raise ValueError('No requirements found. Use requirement IDs and clear shall or must statements.')
            offset = len(state['pages'])
            for page in pages:
                page['page'] += offset
            for record in records:
                record['page'] += offset
        else:
            identifier, title, text = identifier.strip().upper(), title.strip(), text.strip()
            if not re.fullmatch(r'[A-Z][A-Z0-9_-]{1,39}', identifier) or not 1 <= len(title) <= 200 or not 10 <= len(text) <= 12000:
                raise ValueError('Enter a requirement ID, a title, and a description of 10 to 12,000 characters.')
            page = len(state['pages']) + 1
            pages = [{'page': page, 'text': identifier + ' ' + title + '\n' + text}]
            records = [{'id': identifier, 'title': title, 'text': text, 'page': page,
                        'criteria': [], 'status': 'Manual entry'}]
        existing = {r['id'] for r in state['requirements']}
        if existing & {r['id'] for r in records}:
            raise ValueError('A requirement with this ID already exists. Use a different ID.')
        state['pages'].extend(pages)
        state['requirements'].extend(records)
        state['requirements'].sort(key=lambda r: r['id'])
        document = {'name': Path(filename).name if pdf else 'Manual entry', 'ids': [r['id'] for r in records],
                    'hash': digest(pdf if pdf else text.encode()), 'at': now()}
        state.setdefault('requirement_sources', []).append(document)
        if pdf:
            (folder(session_id) / ('requirements-' + uuid4().hex[:8] + '.pdf')).write_bytes(pdf)
        state['pdf_name'] = document['name'] if not state.get('pdf_name') or state['pdf_name'] == 'No requirements' else state['pdf_name']
        state['pdf_hash'] = digest(json.dumps(state['pages'], sort_keys=True).encode())
        state['events'].append({'at': now(), 'action': 'requirements_added', 'count': len(records)})
        save(state)


@trace_operation("APPROVAL", "Review test case")
def review_case(session_id, test_id, action, fields=None):
    with LOCK:
        state = read(session_id)
        if state['status'] not in {'review', 'approved'}:
            raise ValueError('Test cases cannot be changed in the current state.')
        test = next((t for t in state['tests'] if t['id'] == test_id), None)
        if test is None or test.get('review_status') == 'approved' or test_id in (state.get('approval') or {}).get('tests', {}):
            raise ValueError('Only unapproved test cases can be edited or rejected.')
        before = dict(test)
        if action == 'reject':
            test['review_status'] = 'rejected'
        elif action == 'edit':
            fields = fields or {}
            for key, limit in [('title', 200), ('expected', 1500), ('limitations', 1500), ('requirement', 300)]:
                value = fields.get(key, '').strip()
                if not value or len(value) > limit:
                    raise ValueError('Complete every case field within the displayed limits.')
            if fields['requirement'] not in {r['id'] for r in state['requirements']}:
                raise ValueError('Select a requirement from this project.')
            test.update({key: fields[key].strip() for key in ('title', 'expected', 'limitations', 'requirement')})
            test['review_status'] = 'pending'
        else:
            raise ValueError('Unknown review action.')
        state.setdefault('test_history', []).append({'at': now(), 'reason': action, 'tests': [before]})
        test.pop('code', None)
        test.pop('hash', None)
        test.pop('approved_at', None)
        test.update(code_status='not_generated', code_error=None)
        state['events'].append({'at': now(), 'action': 'case_' + action, 'test_ids': [test_id]})
        save(state)


def record_model_trace(state, prompt_name, evidence, response):
    prompt = load_prompt(prompt_name)
    state.setdefault('events', []).append({'at': now(), 'action': 'model_response_recorded',
        'prompt_file': prompt_name, 'prompt_sha256': digest(prompt.encode()),
        'prompt': prompt, 'sources': evidence, 'model': response.get('model'),
        'output': response.get('text'), 'validation': 'Response received; validation follows.'})
    with LOCK:
        save(state)


@trace_operation("AGENT", "Change project connection")
def set_project_connection(session_id, connected):
    """Soft disconnect all snapshots of a project; retain evidence and source files."""
    with LOCK:
        selected = read(session_id)
        def key(state):
            return state.get('project_key') or state['name'] + ':' + state.get('adapter', '')
        states = []
        for path in home().glob('*/session.json'):
            state = json.loads(path.read_text(encoding='utf-8'))
            if key(state) == key(selected):
                states.append(state)
        if any(state['status'] in {'queued', 'running', 'generation_queued', 'generating', 'code_generating'} for state in states):
            raise ValueError('Wait for this project’s current operation to finish before disconnecting.')
        for state in states:
            state['disconnected'] = not connected
            state.setdefault('events', []).append({'at': now(), 'action': 'project_reconnected' if connected else 'project_disconnected'})
            save(state)
