import requests
import os
import bcrypt
import hashlib
import base64

# Global variables
g_recaptcha_secret = os.getenv('recaptcha-secret')


def verify_recaptcha(g_recaptcha_response) -> bool:
    recap_status = requests.post('https://www.google.com/recaptcha/api/siteverify', data={
        'secret': g_recaptcha_secret,
        'response': g_recaptcha_response
    })
    return recap_status.json()['success']


def new_user(email, password):
    # Encode password to allow longer length passwords (limitation of bcrypt = 72 character max length)
    encoded_pass = base64.b64encode(hashlib.sha256(password.encode('utf-8')).digest())
    # Hash encoded password with salt
    # pass_hash includes hash and salt
    pass_hash = bcrypt.hashpw(encoded_pass, bcrypt.gensalt())

    # TODO Add new user to the Users db table


def verify_password(email, password) -> bool:
    # Encode password to allow longer length passwords (limitation of bcrypt = 72 character max length)
    encoded_pass = base64.b64encode(hashlib.sha256(password.encode('utf-8')).digest())

    # TODO Get hashed password from db based on email (check if email exists first)
    # Get hashed password from db
    hashed_pass = b'$2b$12$mrPTNVwF3VYvmmhTfO/mi.BxiMfoSY7bo717veVkq10VCAngzI1fW'

    return bcrypt.checkpw(encoded_pass, hashed_pass)
