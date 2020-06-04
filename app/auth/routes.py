from flask import render_template, redirect, url_for, flash, request, \
    abort, make_response, current_app
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth import bp
from app.auth.forms import *
from app.models import User, AuthSMS
from app.auth.email import send_password_reset_email, send_register_request_email
import jwt, random, string, requests, hmac, hashlib
from time import time
from flask_restful import http_status_message
from datetime import timedelta, datetime

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit() or request.method == 'POST':
        try:
            user = User.query.filter_by(
            username=form.username.data or request.method['username']
            ).first()
            if user is None or \
                not (user.check_password(form.password.data) 
                or user.check_password(request.method['password'])):
                flash('아이디 혹은 비밀번호를 확인해주세요.')
                return redirect(url_for('auth.login'))
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('main.index')
            return redirect(next_page)
        except:
            flash('아이디를 확인해주세요.')
            return redirect(url_for('auth.login'))
    return render_template('auth/login.html', title='Sign In', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
    #return redirect(url_for('main.index'))

@bp.route('/authentication', methods=['GET', 'POST'])
def authentication():    
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        try:
            user_type = request.form['register_type']
            auth_type = request.form['auth_type']
            email_or_number = request.form['email_or_number']
            
            if auth_type == 'email':
                user = User.query.filter_by(email=email_or_number).first()
                if user:
                    flash('등록된 이메일 주소입니다.')
                    return redirect(url_for('auth.login'))
                else:
                    send_register_request_email(email_or_number, positions=user_type)
                    flash('이메일을 확인 후, 가입을 완료해주세요.')
                    return render_template('/auth/authentication.html', email=1)
            elif auth_type == 'phone':
                user = User.query.filter_by(phone=email_or_number).first()
                if user:
                    flash('등록된 휴대폰 번호입니다.')
                    return redirect(url_for('auth.login'))
                else:
                    auth_prev = AuthSMS.query.filter_by(phone_number=email_or_number).first_or_404()
                    if auth_prev:
                        db.session.delete(auth_prev)
                    authsms = AuthSMS(phone_number=email_or_number)
                    authsms.send_sms()
                    db.session.add(authsms)
                    db.session.commit()
                    flash('인증번호가 발송되었습니다.')
                    return render_template('/auth/authentication.html', phone=1, positions=user_type, phone_number=authsms.phone_number)
        except:
            flash('직위, 인증방법 선택과 인증주소 입력은 필수입니다.')
            return redirect(url_for('auth.position'))
    form_auth = Type_Auth()
    return render_template('auth/position.html', form=form_auth)

@bp.route('/authentication_sms/<positions>/<phone_number>', methods=['GET', 'POST'])
def authentication_sms(phone_number, positions):
    authsms = AuthSMS.query.filter_by(phone_number=phone_number).first()
    input_num = request.form['input_auth']    
    
    if authsms.created_time + timedelta(minutes=5) >datetime.utcnow():        
        if authsms.auth_number == int(input_num):            
            return redirect(url_for('auth.register', mail_or_number=phone_number, positions=positions))
        else:            
            flash('인증번호를 다시 입력해주세요.')
    else:        
        flash('시간을 초과하였습니다. 인증번호를 다시 받아주세요.')
        return redirect(url_for('auth.authentication'))
    return render_template('/auth/authentication.html', phone=1, positions=positions, phone_number=authsms.phone_number)

@bp.route('/sign_up/<positions>/<token>', methods=['GET', 'POST'])
def sign_up(token, positions):
    try:
        jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        mail = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['mail']
        return redirect(url_for('auth.register', positions=positions, mail_or_number=mail))
    except jwt.ExpiredSignatureError:
        flash('Your token is expired')
        return redirect(url_for('auth.login'))

@bp.route('/position', methods=['POST', 'GET'])
def position():
    form = Type_Auth()
    return render_template('auth/position.html', form=form)

@bp.route('/register/<positions>/<mail_or_number>', methods=['GET', 'POST'])
def register(positions, mail_or_number):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    form.positions.data = positions
    if '@' in mail_or_number:
        form.email.data = mail_or_number
    else:
        form.phone.data = mail_or_number

    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, birthday=form.birthday.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('회원 가입에 성공하셨습니다!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)

@bp.route('/authentic')
def authentic(positions):
    pass

#제작시 가입 테스트마다 인증받기 번거로워 삽입한 코드, 추후 삭제
@bp.route('/register_auth/', methods=['GET', 'POST'])
def register_auth(positions):
    form = RegistrationForm()   
    
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, birthday=form.birthday.data)
        user.set_password(form.password.data)
        position.users.append(user)
        db.session.add(user)
        db.session.commit()
        flash('회원 가입에 성공하셨습니다!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)

        
#여기에 아이디 찾기도 설정하자?? 아이디를 이메일로 설정하면 필요없을듯??
@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if  current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegisterRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
            flash(
            'Check your email for the instructions to reset your password')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html',
                           title='Reset Password', form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)
