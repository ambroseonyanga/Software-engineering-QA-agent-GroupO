from io import BytesIO
from pathlib import Path
import secrets
import threading

from flask import Blueprint, abort, jsonify, redirect, render_template, request, send_file, session, url_for

try:
    from . import workflow_service as service
    from . import workflow_runner as runner
    from .workflow_report import report_bytes
except ImportError:
    import workflow_service as service
    import workflow_runner as runner
    from workflow_report import report_bytes

workflow = Blueprint('workflow', __name__)


def token():
    if 'workflow_csrf' not in session:
        session['workflow_csrf'] = secrets.token_urlsafe(32)
    return session['workflow_csrf']


@workflow.before_request
def protect():
    if request.method == 'POST':
        expected = session.get('workflow_csrf', '')
        if not expected or not secrets.compare_digest(expected, request.form.get('csrf_token', '')):
            abort(403)


def get_state(session_id):
    try:
        return service.read(session_id)
    except (ValueError, OSError):
        abort(404)


@workflow.route('/workflow', methods=['GET', 'POST'])
def setup():
    error = None
    if request.method == 'POST':
        try:
            upload = request.files.get('requirements_pdf')
            manual = request.form.get('manual_text', '')
            if not manual.strip() and (not upload or not upload.filename):
                raise ValueError('Choose a requirements PDF or enter the requirements manually.')
            state = service.create(upload.read(10_000_001) if upload else b'', upload.filename if upload else '',
                                   request.form.get('code_path', ''), request.form.get('adapter', ''),
                                   request.form.get('focus', ''), manual_text=manual)
            return redirect(url_for('workflow.detail', session_id=state['id'], screen='requirements'))
        except (ValueError, OSError) as exception:
            error = str(exception)
    if request.method == 'GET' and request.args.get('screen') in {'requirements', 'review', 'execution', 'results'}:
        return redirect(url_for('workflow.connect_project'))
    return render_workspace(None, 'projects' if error else screen_name(), error=error,
                            connect_form=bool(error)), 400 if error else 200


@workflow.route('/workflow/<session_id>')
def detail(session_id):
    state = get_state(session_id)
    return render_workspace(state, screen_name(project=True))


@workflow.route('/workflow/<session_id>/generate', methods=['POST'])
def generate(session_id):
    with service.LOCK:
        state = get_state(session_id)
        if state['status'] not in {'ready', 'review', 'generation_failed'}:
            abort(409)
        state['status'] = 'generation_queued'
        service.save(state)
        threading.Thread(target=service.generate, args=(session_id, True), daemon=True).start()
    return redirect(url_for('workflow.project_view', session_id=session_id, section='cases'))


@workflow.route('/workflow/<session_id>/approve', methods=['POST'])
def approve(session_id):
    get_state(session_id)
    try:
        selected = request.form.getlist('tests')
        state = get_state(session_id)
        if state['status'] == 'approved' or any('code' not in test for test in state['tests']):
            service.prepare_approval(session_id, selected)
            threading.Thread(target=service.generate_approved_code, args=(session_id,), daemon=True).start()
        else:
            service.approve(session_id, selected)
    except ValueError as exception:
        state = get_state(session_id)
        return render_workspace(state, 'cases', error=str(exception)), 400
    return redirect(url_for('workflow.project_view', session_id=session_id, section='executions'))


@workflow.route('/workflow/<session_id>/run', methods=['POST'])
def run(session_id):
    get_state(session_id)
    try:
        runner.start(session_id)
    except ValueError as exception:
        state = get_state(session_id)
        return render_workspace(state, 'executions', error=str(exception)), 409
    return redirect(url_for('workflow.project_view', session_id=session_id, section='executions'))


@workflow.route('/workflow/<session_id>/cancel', methods=['POST'])
def cancel(session_id):
    get_state(session_id)
    runner.cancel_run(session_id)
    return redirect(url_for('workflow.project_view', session_id=session_id, section='reports'))


@workflow.route('/workflow/<session_id>/status')
def status(session_id):
    state = get_state(session_id)
    return jsonify(status=state['status'], completed=len(state['results']),
                   selected=len((state.get('approval') or {}).get('tests', {})))


@workflow.route('/workflow/<session_id>/report')
def report(session_id):
    state = get_state(session_id)
    if state['status'] not in {'completed', 'blocked', 'cancelled'}:
        abort(409)
    return send_file(BytesIO(report_bytes(state)), as_attachment=True,
                     download_name='QA-report-' + session_id[:8] + '.docx',
                     mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')


@workflow.route('/workflow/<session_id>/evidence')
def evidence(session_id):
    import json
    state = get_state(session_id)
    return send_file(BytesIO(json.dumps(state, indent=2).encode()), as_attachment=True,
                     download_name='QA-evidence-' + session_id[:8] + '.json', mimetype='application/json')



GLOBAL_VIEWS = {'dashboard': 'Dashboard', 'projects': 'Projects', 'activity': 'Recent Activity', 'settings': 'Settings'}
PROJECT_VIEWS = {'overview': 'Overview', 'requirements': 'Requirements', 'cases': 'Test Cases', 'executions': 'Executions', 'reports': 'Reports'}


def screen_name(project=False):
    screen = request.args.get('screen', 'overview' if project else 'dashboard')
    screen = {'review': 'cases', 'execution': 'executions', 'results': 'reports'}.get(screen, screen)
    if project:
        return screen if screen in PROJECT_VIEWS else 'overview'
    return screen if screen in GLOBAL_VIEWS else 'dashboard'


def catalog():
    import json
    states = []
    for path in service.home().glob('*/session.json'):
        try:
            state = json.loads(path.read_text(encoding='utf-8'))
            if all(k in state for k in ('id', 'name', 'created', 'status')):
                states.append(state)
        except (OSError, ValueError):
            continue
    states.sort(key=lambda s: s['created'], reverse=True)
    groups = {}
    for state in states:
        key = state.get('project_key') or state['name'] + ':' + state.get('adapter', '')
        if key not in groups:
            groups[key] = dict(state, versions=0)
        groups[key]['versions'] += 1
    projects = list(groups.values())
    activity = []
    for state in states:
        events = state.get('events', []) or [{'at': state['created'], 'action': 'session_created'}]
        for event in events:
            activity.append(dict(event, project_name=state['name'], session_id=state['id']))
    activity.sort(key=lambda e: e['at'], reverse=True)
    return projects, states, activity


def render_workspace(state, screen, error=None, **extra):
    import re
    projects, states, activity = catalog()
    metrics = {'projects': len(projects), 'requirements': sum(len(s.get('requirements', [])) for s in projects),
               'cases': sum(len(s.get('tests', [])) for s in projects),
               'executions': sum(bool(s.get('finished')) for s in states)}
    groups = []
    if state:
        remaining = list(state['tests'])
        for requirement in sorted(state.get('requirements', []), key=lambda r: r['id']):
            tests = [t for t in remaining if re.search(r'(?<![A-Za-z0-9_-])' + re.escape(requirement['id']) + r'(?:-AC[0-9]+)?(?![A-Za-z0-9_-])', t['requirement'], re.I)]
            groups.append({'id': requirement['id'], 'title': requirement['title'], 'tests': tests})
            remaining = [t for t in remaining if t not in tests]
        if remaining:
            groups.append({'id': 'Unmapped', 'title': 'Requirement link needs review', 'tests': remaining})
    return render_template('workflow.html', view='workflow', state=state, screen=screen,
                           global_view='projects' if state else screen, error=error,
                           csrf_token=token(), projects=projects, sessions=states, activity=activity,
                           metrics=metrics, groups=groups, project_views=PROJECT_VIEWS,
                           default_path=str(Path.home() / 'Desktop' / 'capstone' / 'BudgetMe'), **extra)


@workflow.route('/dashboard')
def dashboard():
    return render_workspace(None, 'dashboard')


@workflow.route('/projects')
def projects():
    return render_workspace(None, 'projects')


@workflow.route('/activity')
def activity():
    return render_workspace(None, 'activity')


@workflow.route('/settings')
def settings():
    return render_workspace(None, 'settings')


@workflow.route('/projects/new', methods=['GET', 'POST'])
def connect_project():
    error = None
    if request.method == 'POST':
        try:
            state = service.connect(request.form.get('code_path', ''), request.form.get('adapter', ''), request.form.get('name', ''))
            return redirect(url_for('workflow.project_view', session_id=state['id'], section='overview'))
        except (ValueError, OSError) as exception:
            error = str(exception)
    return render_workspace(None, 'projects', error=error, connect_form=True), 400 if error else 200


@workflow.route('/projects/<session_id>/<section>')
def project_view(session_id, section):
    if section not in PROJECT_VIEWS:
        abort(404)
    return render_workspace(get_state(session_id), section)


@workflow.route('/projects/<session_id>/requirements', methods=['POST'])
def add_requirements(session_id):
    get_state(session_id)
    try:
        upload = request.files.get('requirements_pdf')
        service.add_requirements(session_id, identifier=request.form.get('identifier', ''),
            title=request.form.get('title', ''), text=request.form.get('text', ''),
            pdf=upload.read(10000001) if upload and upload.filename else b'', filename=upload.filename if upload else '')
    except (ValueError, OSError) as exception:
        return render_workspace(get_state(session_id), 'requirements', error=str(exception)), 400
    return redirect(url_for('workflow.project_view', session_id=session_id, section='requirements'))


@workflow.route('/projects/<session_id>/cases/<test_id>/<action>', methods=['POST'])
def case_action(session_id, test_id, action):
    get_state(session_id)
    try:
        if action == 'approve':
            service.prepare_approval(session_id, [test_id])
            threading.Thread(target=service.generate_approved_code, args=(session_id,), daemon=True).start()
        else:
            service.review_case(session_id, test_id, action, request.form)
    except ValueError as exception:
        return render_workspace(get_state(session_id), 'cases', error=str(exception)), 400
    return redirect(url_for('workflow.project_view', session_id=session_id,
                            section='executions' if action == 'approve' else 'cases'))


@workflow.route('/projects/<session_id>/issues', methods=['POST'])
def issue_draft(session_id):
    state = get_state(session_id)
    test_id = request.form.get('test_id', '')
    if not any(r['id'] == test_id and r['status'] == 'failed' for r in state['results']):
        abort(409)
    try:
        from .tool_service import invoke_tool
    except ImportError:
        from tool_service import invoke_tool
    result = invoke_tool('create_issue_draft', {key: request.form.get(key, '') for key in ('title', 'failed_test', 'expected', 'actual', 'notes')})
    if not result.get('ok'):
        return render_workspace(state, 'reports', error=result.get('message', 'Draft could not be saved.')), 400
    with service.LOCK:
        state = get_state(session_id)
        state.setdefault('issue_drafts', []).append({'test_id': test_id, 'title': request.form.get('title', ''),
                                                    'path': result.get('path', ''), 'at': service.now()})
        state['events'].append({'at': service.now(), 'action': 'issue_draft_saved', 'test_ids': [test_id]})
        service.save(state)
    return redirect(url_for('workflow.project_view', session_id=session_id, section='reports'))


@workflow.route('/projects/<session_id>/analysis/<test_id>', methods=['POST'])
def analyze_failure(session_id, test_id):
    state = get_state(session_id)
    result = next((r for r in state['results'] if r['id'] == test_id and r['status'] not in {'passed', 'skipped'}), None)
    test = next((t for t in state['tests'] if t['id'] == test_id), None)
    if result is None or test is None:
        abort(409)
    try:
        from .agent import run_agent
        from .app import history_store
    except ImportError:
        from agent import run_agent
        from app import history_store
    analysis = run_agent({'title': ('Failure: ' + test['title'])[:120], 'failed_test': test_id,
                          'expected': test['expected'][:1000],
                          'actual': ((result.get('detail') or '') + '\n' + result['output'])[:1000]},
                         memory_store=history_store(), use_history=False)
    with service.LOCK:
        state = get_state(session_id)
        state.setdefault('failure_analyses', {})[test_id] = {
            'at': service.now(), 'message': analysis.get('message', ''),
            'steps': analysis.get('steps', []), 'sources': analysis.get('linked_sources', []),
            'stop_reason': analysis.get('stop_reason', '')}
        if analysis.get('draft'):
            state.setdefault('issue_drafts', []).append({'test_id': test_id, 'title': test['title'],
                                                       'path': analysis['draft'].get('path', ''), 'at': service.now()})
        state['events'].append({'at': service.now(), 'action': 'failure_analyzed', 'test_ids': [test_id]})
        service.save(state)
    return redirect(url_for('workflow.project_view', session_id=session_id, section='reports'))
