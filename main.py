from flask import Flask, jsonify, request, session, redirect
from functools import wraps
from flask_cors import CORS
import os
import sys
import datetime

from src import auth
from src import db

app = Flask(__name__)
app.secret_key = os.getenv('SESSION_SECRET')
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=1)
cors = CORS(app)


@app.after_request
def add_header(response):
    response.headers.add("Access-Control-Allow-Origin", "https://camping.sebtota.com")
    response.headers.add("Access-Control-Allow-Credentials", "true")
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
            return redirect('login.html')

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
        # Set expiration date on sign in cookie
        session.permanent = True
        expire_date = datetime.datetime.now() + datetime.timedelta(days=1)
        # Password is correct, return temporary session ID
        username_query = db.get_username_by_email(email)
        if username_query['found']:
            session['email'] = email

            profile_query = db.get_profile_by_email(email)
            resp = jsonify({'status': 200, 'email': email})
            resp.set_cookie('active', 'true', expires=expire_date)

            for k, v in profile_query['profile'].items():
                resp.set_cookie(k, v, expires=expire_date)

            return resp
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


@app.route('/logout', methods=['POST'])
def logout():
    print(session, file=sys.stdout)
    resp = jsonify({'status': 200})
    session.pop('email', None)
    resp.set_cookie('active', 'false')
    return resp


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
@user_check
def get_group_invites():
    user_email = session.get('email', None)
    if user_email is None:
        return jsonify({'status': 400})

    return jsonify({'status': 200, 'invites': db.get_group_requests(user_email)})


@app.route('/acceptGroupInvite', methods=['POST'])
@user_check
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
@user_check
def decline_group_invite():
    data = request.get_json(force=True)

    if 'request-uuid' in data:
        db.remove_group_invite_request(data['request-uuid'])
        return jsonify({'status': 200})
    else:
        # Missing request uuid so nothing to decline
        return jsonify({'status': 400, 'error': 'missing-uuid'})


@app.route('/getGroupsByUser', methods=['GET'])
@user_check
def get_group_by_user():
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

def get_groups_by_user():
    user_email = session.get('email', None)

    if user_email is None:
        return jsonify({'status': 400})
    else:
        return jsonify({'status': 200,
                        'groups': db.get_group_uuid_by_user(user_email)
                        })


@app.route('/getListsByGroup', methods=['GET'])
def get_lists_by_group():
    group_uuid = request.args.get("group-uuid")

    if group_uuid:
        return jsonify({'status': 200,
                        'lists': db.get_lists_in_group(group_uuid)})
    else:
        return jsonify({'status': 400})


@app.route('/deleteSelfFromGroup', methods=['POST'])
def delete_self_from_group():
    group_uuid = request.args.get("group-uuid")
    user_email = session.get('email', None)

    if group_uuid:
        db.delete_user_from_group(user_email, group_uuid)
        return jsonify({'status': 200})
    else:
        return jsonify({'status': 400})


@app.route('/renameGroup', methods=['POST'])
def rename_group():
    data = request.get_json(force=True)
    group_uuid = data.get("group-uuid")

    if group_uuid:
        db.rename_group(data["new-name"], group_uuid)
        return jsonify({'status': 200})
    else:
        return jsonify({'status': 400})


@app.route('/getElementsByList', methods=['GET'])
def get_elements_by_list():
    list_uuid = request.args.get("list-uuid")

    if list_uuid:
        return jsonify(({'status': 200,
                         'elements': db.get_items_in_list(list_uuid)}))
    else:
        return jsonify(({'status': 400,
                         'elements': 'list_uuid does not exist'}))


@app.route('/deleteElementFromList', methods=['POST'])
def delete_element_from_list():
    element_uuid = request.args.get("element-uuid")

    if element_uuid:
        return jsonify(({'status': 200,
                         'elements': db.remove_item_from_list(element_uuid)}))
    else:
        return jsonify(({'status': 400,
                         'elements': 'elements_uuid does not exist'}))


@app.route('/addElementToList', methods=['POST'])
def add_element_to_list():
    data = request.get_json(force=True)
    list_id = data['list-id']
    element_name = data['element-name']
    element_description = data['element-description']
    element_user_id = data['element-user-id']
    element_quantity = data['element-quantity']
    element_cost = data['element_cost']
    element_status = data['element_status']

    if list_id and element_name and element_description and element_user_id and element_quantity and element_cost and element_status:
        return jsonify({'status': 200,
                        'elements': db.add_item_to_list(list_id, element_name, element_description, element_user_id,
                                                        element_quantity, element_cost, element_status)})
    else:
        return jsonify({'status': 400,
                        'elements': 'required data not provided or does not exist'})


@app.route('/claimItem', methods=['POST'])
def claim_item():
    element_uuid = request.args.get("element-uuid")
    user_email = request.args.get("user-email")  # session.get('email', None)
    print(user_email)
    if element_uuid and user_email:
        return jsonify({'status': 200,
                        'elements': db.claim_item(element_uuid, user_email)})
    else:
        return jsonify({'status': 400,
                        'elements': 'could not claim item, could not find element_uuid'})


@app.route('/unClaimItem', methods=['POST'])
def unclaim_item():
    element_uuid = request.args.get("element-uuid")

    if element_uuid:
        return jsonify({'status': 200,
                        'elements': db.unclaim_item(element_uuid)})
    else:
        return jsonify({'status': 400,
                        'elements': 'could not unclaim item, could not find element_uuid'})


@app.route('/updateItemStatus', methods=['POST'])
def update_item_status():
    element_status = request.args.get("element-status")
    element_uuid = request.args.get("element-uuid")

    if element_uuid and element_status:
        return jsonify({'status': 200,
                        'elements': db.update_item_status(element_uuid, element_status)})
    else:
        return jsonify({'status': 400,
                        'elements': 'could not update element status'})


@app.route('/renameItem', methods=['POST'])
def rename_item():
    data = request.get_json(force=True)
    element_uuid = data.get("element-uuid")

    if element_uuid:
        db.rename_item(data["new-name"], element_uuid)
        return jsonify({'status': 200})
    else:
        return jsonify({'status': 400})


@app.route('/changeItemCost', methods=['POST'])
def change_item_cost():
    data = request.get_json(force=True)
    element_uuid = data.get("element-uuid")

    if element_uuid:
        db.change_cost_of_item(data["new-cost"], element_uuid)
        return jsonify({'status': 200})
    else:
        return jsonify({'status': 400})


@app.route('/changeItemDescription', methods=['POST'])
def change_item_description():
    data = request.get_json(force=True)
    element_uuid = data.get("element-uuid")

    if element_uuid:
        db.change_item_description(data["new-description"], element_uuid)
        return jsonify({'status': 200})
    else:
        return jsonify({'status': 400})


@app.route('/getItemById', methods=['GET'])
def get_item_by_id():
    element_uuid = request.args.get("element-uuid")

    if element_uuid:
        return jsonify(({'status': 200,
                         'elements': db.get_item_by_id(element_uuid)}))
    else:
        return jsonify(({'status': 400,
                         'elements': 'element_uuid does not exist'}))


@app.route('/createList', methods=['POST'])
def create_list():
    data = request.get_json(force=True)
    group_id = db.get_group_id_by_uuid(data.get("group-uuid"));

    if group_id:
        db.create_list(data["name"], group_id)
        return jsonify({'status': 200})
    else:
        return jsonify({'status': 400})


@app.route('/deleteList', methods=['POST'])
def delete_list():
    data = request.get_json(force=True)
    list_uuid = data.get("list-uuid")

    if list_uuid:
        db.delete_list_by_id(list_uuid)
        return jsonify({'status': 200})
    else:
        return jsonify({'status': 400})


@app.route('/renameList', methods=['POST'])
def rename_list():
    data = request.get_json(force=True)
    list_uuid = data.get("list-uuid")

    if list_uuid:
        db.rename_list(data["new-name"], list_uuid)
        return jsonify({'status': 200})
    else:
        return jsonify({'status': 400})


@app.route('/getUsersInGroup', methods=['GET'])
def get_users_in_group():
    group_uuid = request.args.get("group_uuid")

    print(group_uuid)

    if group_uuid:
        return jsonify({'status': 200, 'users': db.get_all_users_in_group(group_uuid)})
    return jsonify({'status': 400})

@app.route('/createGroup', methods=['POST'])
def create_group():
    data = request.get_json(force=True)
    group_name = data.get('group-name')
    user_email = session.get('email', None)

    if group_name:
        group_uuid = db.create_group(group_name)
        db.add_user_to_group(db.get_group_id_by_uuid(group_uuid), db.get_user_id_by_email(user_email))

        return jsonify({'status': 200})
    else:
        return jsonify({'status': 400})


@app.route('/addUserToGroup', methods=['POST'])
def add_user_to_group():
    data = request.get_json(force=True)
    user_email = session.get('email', None)
    group_uuid = data.get("group-uuid")

    if user_email and group_uuid:
        db.add_user_to_group(db.get_group_id_by_uuid(group_uuid), db.get_user_id_by_email(user_email))
        return jsonify({'status': 200})
    else:
        return jsonify({'status': 400})


if __name__ == '__main__':
    cert = os.getenv('DOMAIN_CERT')
    key = os.getenv('PRIVATE_KEY')

    app.run()

    # if cert is None or key is None:
    #     app.run(debug=True, host='0.0.0.0')
    # else:
    #     app.run(debug=True, host='0.0.0.0', ssl_context=(cert, key))
