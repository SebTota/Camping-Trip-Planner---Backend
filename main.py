from flask import Flask, jsonify, request, session, redirect
from functools import wraps
from flask_cors import CORS, cross_origin
import os
import sys
from flask_session import Session
import uuid
import time

from src import auth
from src import db

# name = request.headers["name"]  # localhost:5000/login headers= {'name': 'someones name}
# name = request.args["name"]  # localhost:5000/login?name=sebastian

app = Flask(__name__)
app.secret_key = os.getenv('SESSION_SECRET')
# app.config.from_object(__name__)
cors = CORS(app)


@app.after_request
def add_header(response):
    response.headers.add("Access-Control-Allow-Origin", "https://camping.sebtota.com")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    # response.headers.add('Access-Control-Request-Headers', 'access-control-allow-credentials, access-control-allow-origin')
    # response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    # response.headers.add('CORS_SUPPORTS_CREDENTIALS', 'true')
    # response.headers['Access-Control-Allow-Credentials'] = 'true'
    # response.headers['CORS_SUPPORTS_CREDENTIALS'] = 'true'
    return response


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
        user_session = session.get('email', None)

        if user_session is None:
            return jsonify({'status': 401, 'error': 'no-session-found'})

        return protected_function(*args, **kwargs)

    return wrapper


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
        username_query = db.get_username_by_email(email)
        if username_query['found']:
            session['email'] = email
            return jsonify({'status': 200, 'email': email}), 200
        else:
            return jsonify({'status': 404, 'error': 'user-email-not-found'}), 404
    else:
        # Incorrect password specified, return Unauthorized Code
        return jsonify({'status': 401, 'error': 'incorrect-password'}), 401


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

    if db.check_if_user_exists_by_email(email):
        return jsonify({'status': 400, 'error': 'user-already-exists'})
    else:
        db.sign_up_db(first_name, last_name, email, auth.hash_pass(password))
        session['email'] = email
        return jsonify({'status': 200})


@app.route('/forgotPassword', methods=['POST'])
def forgot_password():
    return ""


@app.route('/checkLogin', methods=['GET'])
def check_login():
    if 'email' not in session:
        return jsonify({'status': 401, 'error': 'no-session-found'}), 200

    user_session = session.get('email', '')

    if user_session != '':
        profile_query = db.get_profile_by_email(user_session)
        if profile_query['found']:
            return jsonify({"status": 200, "profile": profile_query['profile']}), 200

    return jsonify({'status': 401, 'error': 'no-session-found'}), 200


@app.route('/logout', methods=['POST'])
def logout():
    print(session, file=sys.stdout)
    session.pop('email', None)
    return jsonify({'status': 200}), 200


@app.route('/inviteUser', methods=['POST'])
@user_check
def invite_user():
    data = request.get_json(force=True)
    from_user_email = session.get('email', '')
    to_user_email = data['invite-user-email']
    group_uuid = data['group-uuid']

    if from_user_email == '' or to_user_email == '' or group_uuid == '':
        return jsonify({'status': 400})

    db.add_group_request(from_user_email, to_user_email, group_uuid)
    return jsonify({'status': 200})


@app.route('/getGroupInvites', methods=['GET'])
def get_group_invites():
    user_email = session.get('email', None)
    if user_email is None:
        return jsonify({'status': 400})

    return jsonify({'status': 200, 'invites': db.get_group_requests(user_email)})


@app.route('/acceptGroupInvite', methods=['POST'])
def accept_group_invite():
    data = request.get_json(force=True)

    user_email = session.get('email', None)
    if user_email is None:
        return jsonify({'status': 400})

    if 'request-uuid' in data:
        db.accept_group_invite_request(user_email, data['request-uuid'])
        return jsonify({'status': 200})
    else:
        # Missing request uuid so nothing to decline
        return jsonify({'status': 400, 'error': 'missing-uuid'})


@app.route('/declineGroupInvite', methods=['POST'])
def decline_group_invite():
    data = request.get_json(force=True)

    if 'request-uuid' in data:
        db.remove_group_invite_request(data['request-uuid'])
        return jsonify({'status': 200})
    else:
        # Missing request uuid so nothing to decline
        return jsonify({'status': 400, 'error': 'missing-uuid'})


@app.route('/getGroupsByUser', methods=['GET'])
def get_group_by_user():
    user_email = session.get('email', None)

    if user_email is None:
        return jsonify({'status': 400})
    else:
        return jsonify({'status': 200,
                        'groups': [
                            {
                                'group-name': 'Testing Group',
                                'group-uuid': 'ba36f7ca-e8d2-42f9-9b65-ec9dc9fc51f2'
                            },
                            {
                                'group-name': 'Testing Group 2',
                                'group-uuid': '2194d399-b955-49d3-a242-4eebbc4f8d23'
                            }
                        ]
                        })


if __name__ == '__main__':
    cert = os.getenv('DOMAIN_CERT')
    key = os.getenv('PRIVATE_KEY')

    if cert is None or key is None:
        app.run(debug=True, host='0.0.0.0')
    else:
        app.run(debug=True, host='0.0.0.0', ssl_context=(cert, key))
