from flask import Flask, jsonify, request, session, redirect
from functools import wraps
from flask_cors import CORS
import os
from flask_session import Session

from src import auth
from src import db

# name = request.headers["name"]  # localhost:5000/login headers= {'name': 'someones name}
# name = request.args["name"]  # localhost:5000/login?name=sebastian

app = Flask(__name__)
app.secret_key = os.getenv('SESSION_SECRET')
CORS(app)


# Verify recaptcha is authenticated before checking password (prevent bot spamming)
def captcha_check(protected_function):
    @wraps(protected_function)
    def wrapper(*args, **kwargs):
        # Skip check on localhost
        if request.remote_addr == '127.0.0.1':
            return protected_function(*args, **kwargs)

        data = request.get_json(force=True)  # Force body to be read as JSON
        g_recaptcha_response = data.get('recap_response')

        # Verify recaptcha is authenticated before checking password (prevent bot spamming)
        if not auth.verify_recaptcha(g_recaptcha_response):
            # Failed re-captcha verification
            return jsonify({'status': 401, 'error': 'failed-recaptcha'})

        return protected_function(*args, **kwargs)

    return wrapper


# Verify user is signed in before allowing access to endpoint
def user_check(protected_function):
    @wraps(protected_function)
    def wrapper(*args, **kwargs):
        user_session = session.get('username', '')

        if user_session == '':
            return jsonify({'status': 401, 'error': 'no-session-found'})

        return protected_function(*args, **kwargs)
    return wrapper


@app.after_request
def add_header(response):
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response


@app.route('/', methods=['GET'])
def main_page():
    return "Camping Trip Planner Home"


@app.route('/home', methods=['GET'])
def home():
    return jsonify({'name': 'Sebastian Tota'})


@app.route('/login', methods=['POST'])
@captcha_check
def login():
    data = request.get_json(force=True)  # Force body to be read as JSON
    email = data.get('email')
    password = data.get('password')

    # Authenticate users account and password
    if auth.verify_password(email, password):
        # Password is correct, return temporary session ID
        session['username'] = 'testUsername'
        return jsonify({'status': 200, 'email': email, 'session_id': '123abc456def'})
    else:
        # Incorrect password specified, return Unauthorized Code
        return jsonify({'status': 401, 'error': 'incorrect-password'})


@app.route('/signup', methods=['POST'])
@captcha_check
def signup():
    data = request.get_json(force=True)  # Force body to be read as JSON
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    password = data.get('password')
    password_conf = data.get('password_conf')

    # Assert password and password confirmation input is the same
    if password != password_conf:
        return jsonify({'status': 400, 'error': 'failed-password-confirmation'})

    # TODO check if email already exists in the db
    if db.check_if_user_exists_by_email(email):
        return jsonify({'status': 400, 'error': 'user-already-exists'})
    else:
        db.sign_up_db(first_name, last_name, email, password)
        # db.get_password(email)

    return ""


@app.route('/logout')
def logout():
    session.pop('username', None)
    return jsonify({'status': 200})


@app.route('/forgotPassword', methods=['POST'])
def forgot_password():
    return ""


@user_check
@app.route('/checkLogin', methods=['GET'])
def check_login():
    return jsonify({"status": 200})


if __name__ == '__main__':
    cert = os.getenv('DOMAIN_CERT')
    key = os.getenv('PRIVATE_KEY')

    if cert is None or key is None:
        app.run(debug=True, host='0.0.0.0')
    else:
        app.run(debug=True, host='0.0.0.0', ssl_context=(cert, key))
