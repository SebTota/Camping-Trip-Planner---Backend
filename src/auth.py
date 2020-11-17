import requests
from flask import request
import os
import bcrypt
import hashlib
import base64

from src import db

# Global variables
g_recaptcha_secret = os.getenv('RECAPTCHA_SECRET')
if g_recaptcha_secret == '':
    print("ERROR: missing recaptcha secret")
    exit(-1)


def verify_recaptcha(g_recaptcha_response) -> bool:
    recap_status = requests.post('https://www.google.com/recaptcha/api/siteverify', data={
        'secret': g_recaptcha_secret,
        'response': g_recaptcha_response
    })
    return recap_status.json()['success']


def hash_pass(password):
    # Encode password to allow longer length passwords (limitation of bcrypt = 72 character max length)
    encoded_pass = base64.b64encode(hashlib.sha256(password.encode('utf-8')).digest())
    # Hash encoded password with salt
    # pass_hash includes hash and salt
    return bcrypt.hashpw(encoded_pass, bcrypt.gensalt())


def verify_password(email, password) -> bool:
    # Encode password to allow longer length passwords (limitation of bcrypt = 72 character max length)
    encoded_pass = base64.b64encode(hashlib.sha256(password.encode('utf-8')).digest())

    # Get hashed password from db
    password_query = db.get_pass_by_email(email)
    # Check if user is found before verifying password
    if password_query['found']:
        return bcrypt.checkpw(encoded_pass, password_query['pass'].encode('utf-8'))

    return False
