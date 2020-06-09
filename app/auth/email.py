from flask import render_template, current_app
from flask_babel import _
from app.email import send_email
from threading import Thread
import jwt
from time import time
def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[Mathmocha] Reset Your Password',
               sender=current_app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))

def get_register_request_token(mail, expires_in=600):
        return jwt.encode(
            {'mail': mail, 'iss': 'mathmocha', 'exp':time()+expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

def send_register_request_email(mail, positions):
    token = get_register_request_token(mail)
    send_email('[Mathmocha] Sign up!',
               sender=current_app.config['ADMINS'][0],
               recipients=[mail],
               text_body=render_template('email/sign_up.txt',
                                        positions = positions,
                                        token=token),
               html_body=render_template('email/sign_up.html',
                                        positions = positions,
                                        token=token))