from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os

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

klubbar_list = [
    {'nafn': 'Fighting Game Klúbbur', 'stofa': '203', 'formadur': 'Matt', 'desc': 'Klúbbur fyrir alla sem hafa áhuga á bardaga tölvuleikjum.'},
    {'nafn': 'Furry Klúbbur', 'stofa': '206', 'formadur': 'Aron', 'desc': 'Klúbbur fyrir alla sem hafa áhuga á furry menningu.'},
    {'nafn': 'Tónlistarklúbbur', 'stofa': 'Hátíðarsalur', 'formadur': 'Emily', 'desc': 'Klúbbur fyrir alla sem hafa áhuga á tónlist og spilamennsku.'},
    {'nafn': 'Nördaklúbbur', 'stofa': '202', 'formadur': 'Ösp og Kormákur', 'desc': 'Klúbbur fyrir alla nörda og áhugafólk um ýmislegt nördalegt.'},
    {'nafn': 'Anime og Cosplay Klúbbur', 'stofa': '205', 'formadur': 'Sky', 'desc': 'Klúbbur fyrir alla sem hafa áhuga á anime og cosplay.'},
    {'nafn': 'Warhammer Klúbbur', 'stofa': '302', 'formadur': '???', 'desc': 'Klúbbur fyrir alla sem hafa áhuga á Warhammer borðspilinu.'},
    {'nafn': 'D&D Klúbbur', 'stofa': 'fer eftir hóp', 'formadur': 'Frosti', 'desc': 'Klúbbur fyrir alla sem hafa áhuga á Dungeons & Dragons borðspilinu.'}
]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/klubbar')
def klubbar():
    return render_template('klubbar.html', k = klubbar_list)

@app.route('/dagskra')
def dagskra():
    return render_template('dagskra.html')

@app.route('/login', methods=['POST'])
def login():
    username = (request.form.get('username') or '').strip()
    password = request.form.get('password') or ''

    users = _load_users()
    record = users.get(username)
    if record and check_password_hash(record.get('password_hash', ''), password):
        session['user'] = username
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
                    'password_hash': generate_password_hash(password)
                }
                _save_users(users)
                session['user'] = username
                return redirect(url_for('home'))

        # GET or error path
        return render_template('register.html', error=error, pref_username=username)

    return render_template('register.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
