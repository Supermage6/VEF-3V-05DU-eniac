from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import time
from access import DEFAULT_ROLE, ROLE_STUDENT, ROLE_ADMIN  # default role and roles
from access import is_student, current_role, require_roles

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

# --- Simple JSON user store ---
USERS_FILE = 'users.json'

def _load_users():
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def _save_users(users: dict):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

CLUBS_FILE = 'klubbar.json'
PROPOSALS_FILE = 'proposals.json'
SCHEDULE_SETTINGS_FILE = 'schedule_settings.json'

_DEFAULT_CLUBS = [
    {'nafn': 'Fighting Game Klúbbur', 'stofa': '203', 'formadur': 'Matt', 'desc': 'Klúbbur fyrir alla sem hafa áhuga á bardaga tölvuleikjum.'},
    {'nafn': 'Furry Klúbbur', 'stofa': '206', 'formadur': 'Aron', 'desc': 'Klúbbur fyrir alla sem hafa áhuga á furry menningu.'},
    {'nafn': 'Tónlistarklúbbur', 'stofa': 'Hátíðarsalur', 'formadur': 'Emily', 'desc': 'Klúbbur fyrir alla sem hafa áhuga á tónlist og spilamennsku.'},
    {'nafn': 'Nördaklúbbur', 'stofa': '202', 'formadur': 'Ösp og Kormákur', 'desc': 'Klúbbur fyrir alla nörda og áhugafólk um ýmislegt nördalegt.'},
    {'nafn': 'Anime og Cosplay Klúbbur', 'stofa': '205', 'formadur': 'Sky', 'desc': 'Klúbbur fyrir alla sem hafa áhuga á anime og cosplay.'},
    {'nafn': 'Warhammer Klúbbur', 'stofa': '302', 'formadur': '???', 'desc': 'Klúbbur fyrir alla sem hafa áhuga á Warhammer borðspilinu.'},
    {'nafn': 'D&D Klúbbur', 'stofa': 'fer eftir hóp', 'formadur': 'Frosti', 'desc': 'Klúbbur fyrir alla sem hafa áhuga á Dungeons & Dragons borðspilinu.'}
]

def _load_clubs():
    try:
        with open(CLUBS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return list(_DEFAULT_CLUBS)

def _save_clubs(clubs: list):
    with open(CLUBS_FILE, 'w', encoding='utf-8') as f:
        json.dump(clubs, f, ensure_ascii=False, indent=2)

def _load_proposals():
    try:
        with open(PROPOSALS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return []

def _save_proposals(items: list):
    with open(PROPOSALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def _load_schedule_settings() -> dict:
    try:
        with open(SCHEDULE_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    # Default: highlight Wednesdays in green
    return {
        'wed_color': 'green',
        'weekday_colors': { '3': 'green' }  # 0=Sun .. 6=Sat
    }

def _save_schedule_settings(settings: dict) -> None:
    with open(SCHEDULE_SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/klubbar')
def klubbar():
    clubs = _load_clubs()
    is_admin = (session.get('role') == ROLE_ADMIN)
    # Expose student flag so template can gate the create button
    is_student_flag = (session.get('role') == ROLE_STUDENT)
    return render_template('klubbar.html', k=clubs, is_admin=is_admin, is_student=is_student_flag)

@app.route('/info')
@require_roles(ROLE_ADMIN)
def info():
    proposals = _load_proposals()
    return render_template('info.html', proposals=proposals)

@app.route('/klubbar/propose', methods=['GET', 'POST'])
@require_roles(ROLE_STUDENT, ROLE_ADMIN)
def klubbar_propose():
    if request.method == 'POST':
        name = (request.form.get('nafn') or '').strip()
        stofa = (request.form.get('stofa') or '').strip()
        formadur = (request.form.get('formadur') or '').strip()
        desc = (request.form.get('desc') or '').strip()
        if name:
            proposals = _load_proposals()
            pid = str(int(time.time() * 1000))
            proposals.append({
                'id': pid,
                'nafn': name,
                'stofa': stofa,
                'formadur': formadur,
                'desc': desc,
                'submitted_by': session.get('user') or 'unknown',
                'status': 'pending',
            })
            _save_proposals(proposals)
        return redirect(url_for('home'))
    return render_template('klubbar_propose.html')

@app.route('/admin/proposals/<pid>/approve', methods=['POST'])
@require_roles(ROLE_ADMIN)
def admin_proposal_approve(pid):
    proposals = _load_proposals()
    remaining = []
    approved = None
    for p in proposals:
        if str(p.get('id')) == str(pid):
            approved = p
        else:
            remaining.append(p)
    if approved:
        clubs = _load_clubs()
        clubs.append({
            'nafn': approved.get('nafn', ''),
            'stofa': approved.get('stofa', ''),
            'formadur': approved.get('formadur', ''),
            'desc': approved.get('desc', ''),
        })
        _save_clubs(clubs)
        _save_proposals(remaining)
    return redirect(url_for('info'))

@app.route('/admin/proposals/<pid>/deny', methods=['POST'])
@require_roles(ROLE_ADMIN)
def admin_proposal_deny(pid):
    proposals = _load_proposals()
    remaining = [p for p in proposals if str(p.get('id')) != str(pid)]
    _save_proposals(remaining)
    return redirect(url_for('info'))

@app.route('/admin/map/save', methods=['POST'])
@require_roles(ROLE_ADMIN)
def admin_map_save():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or 'floors' not in data:
        return ('Invalid payload', 400)
    # Save to static/map_rooms.json so frontend can fetch it
    static_dir = app.static_folder or 'static'
    path = os.path.join(static_dir, 'map_rooms.json')
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        return ('Failed to write map file', 500)
    return ('OK', 200)

@app.route('/klubbar/edit', methods=['GET', 'POST'])
@require_roles(ROLE_ADMIN)
def klubbar_edit():
    clubs = _load_clubs()
    if request.method == 'POST':
        # Expect fields like name_0, desc_0
        updated = []
        for idx, c in enumerate(clubs):
            name = (request.form.get(f'name_{idx}') or c.get('nafn') or '').strip()
            stofa = (request.form.get(f'stofa_{idx}') or c.get('stofa') or '').strip()
            desc = (request.form.get(f'desc_{idx}') or c.get('desc') or '').strip()
            updated.append({
                'nafn': name,
                'stofa': stofa,
                'formadur': c.get('formadur', ''),
                'desc': desc,
            })
        _save_clubs(updated)
        return redirect(url_for('klubbar'))
    return render_template('klubbar_edit.html', k=clubs)


@app.route('/klubbar/remove', methods=['POST'])
@require_roles(ROLE_ADMIN)
def klubbar_remove():
    idx_raw = request.form.get('idx')
    try:
        idx = int(idx_raw)
    except (TypeError, ValueError):
        return redirect(url_for('klubbar_edit'))
    clubs = _load_clubs()
    if 0 <= idx < len(clubs):
        clubs.pop(idx)
        _save_clubs(clubs)
    return redirect(url_for('klubbar_edit'))


@app.route('/admin/create_user', methods=['POST'])
@require_roles(ROLE_ADMIN)
def admin_create_user():
    username = (request.form.get('username') or '').strip()
    password = request.form.get('password') or ''
    role = (request.form.get('role') or ROLE_STUDENT).strip().lower()

    error = None
    if not username or not password:
        error = 'Username and password are required.'
    elif role not in {ROLE_STUDENT, ROLE_ADMIN}:
        error = 'Invalid role.'
    else:
        users = _load_users()
        if username in users:
            error = 'Username already exists.'
        else:
            users[username] = {
                'password_hash': generate_password_hash(password),
                'role': role,
            }
            _save_users(users)
            return redirect(url_for('klubbar_edit'))

    # On error, just bounce back for now. Could flash error.
    return redirect(url_for('klubbar_edit'))

@app.route('/admin/remove_user', methods=['POST'])
@require_roles(ROLE_ADMIN)
def admin_remove_user():
    username = (request.form.get('username') or '').strip()
    if not username:
        return redirect(url_for('klubbar_edit'))
    # Avoid removing yourself from within the UI
    if session.get('user') and session['user'].lower() == username.lower():
        return redirect(url_for('klubbar_edit'))
    users = _load_users()
    if username in users:
        users.pop(username)
        _save_users(users)
    return redirect(url_for('klubbar_edit'))

@app.route('/dagskra')
def dagskra():
    settings = _load_schedule_settings()
    is_admin = (session.get('role') == ROLE_ADMIN)
    return render_template(
        'dagskra.html',
        wed_color=settings.get('wed_color', 'green'),
        weekday_colors=settings.get('weekday_colors', {}),
        is_admin=is_admin,
    )

@app.route('/admin/schedule/highlight', methods=['POST'])
@require_roles(ROLE_ADMIN)
def admin_schedule_highlight():
    color = (request.form.get('color') or '').strip().lower()
    if color not in {'green', 'red'}:
        color = 'green'
    settings = _load_schedule_settings()
    settings['wed_color'] = color
    _save_schedule_settings(settings)
    return redirect(url_for('dagskra'))

@app.route('/admin/schedule/colors', methods=['POST'])
@require_roles(ROLE_ADMIN)
def admin_schedule_colors():
    allowed = {'none', 'green', 'red', 'blue', 'yellow', 'purple'}
    colors = {}
    for i in range(7):
        val = (request.form.get(f'color_{i}') or 'none').strip().lower()
        colors[str(i)] = val if val in allowed else 'none'
    settings = _load_schedule_settings()
    settings['weekday_colors'] = colors
    _save_schedule_settings(settings)
    return redirect(url_for('dagskra'))

@app.route('/login', methods=['POST'])
def login():
    username = (request.form.get('username') or '').strip()
    password = request.form.get('password') or ''

    users = _load_users()
    record = users.get(username)
    if record and check_password_hash(record.get('password_hash', ''), password):
        # Respect stored role if present; if missing, infer default
        stored_role = record.get('role')
        if not stored_role:
            stored_role = ROLE_ADMIN if username.lower() == 'knut' else ROLE_STUDENT
            record['role'] = stored_role
            users[username] = record
            _save_users(users)
        session['user'] = username
        session['role'] = stored_role
        session['display_name'] = 'admin' if stored_role == ROLE_ADMIN else username
    # On failure, silently fall through to home. Could add errors if desired.
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        password2 = request.form.get('password2') or ''

        error = None
        if not username or not password:
            error = 'Username and password are required.'
        elif password != password2:
            error = 'Passwords do not match.'
        else:
            users = _load_users()
            if username in users:
                error = 'Username already exists.'
            else:
                users[username] = {
                    'password_hash': generate_password_hash(password),
                    'role': DEFAULT_ROLE,
                }
                _save_users(users)
                session['user'] = username
                session['role'] = DEFAULT_ROLE
                session['display_name'] = username
                return redirect(url_for('home'))

        # GET or error path
        return render_template('register.html', error=error, pref_username=username)

    return render_template('register.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    session.pop('role', None)
    session.pop('display_name', None)
    return redirect(url_for('home'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
