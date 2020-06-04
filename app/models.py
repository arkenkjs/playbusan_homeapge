from datetime import datetime, timedelta
from flask_login import UserMixin 
from app import login, db
from flask import current_app, url_for 
import requests, jwt, base64, os, json
from random import randint
from time import time
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5
from sqlalchemy import and_

class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links':{
                'self': url_for(endpoint, page=page, per_page=per_page, **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page, 
                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                 **kwargs) if resources.has_prev else None,
            }            
        }
        return data


class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer(), primary_key=True)
    categories = db.Column(db.String(20), unique=True)
    categories_description = db.Column(db.String(20))    
    def __str__(self):
        return self.categories

class User(PaginatedAPIMixin, UserMixin, db.Model):
    __tablename__ = 'user'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    birthday = db.Column(db.Date)
    phone = db.Column(db.Text(20))
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140), nullable=True)
    token=db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)    

    boards = db.relationship('Board', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')    
    
    message_sent = db.relationship('Message',
                                   foreign_keys='Message.sender_id',
                                   backref='author', lazy='dynamic')
    messages_received = db.relationship('Message',
                                        foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')


    def __str__(self):
        return self.email
    
    def __repr__(self):
        return '<User {}>'.format(self.username)
        
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token
    
    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user
                
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password':self.id, 'exp':time()+expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']        
        except:
            return 
        return User.query.get(id)

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(
            Message.timestamp > last_read_time).count()
    
    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n
    

class Message(db.Model, PaginatedAPIMixin):
    __tablename__ = 'message'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    
    def __repr__(self):
        return '<Message {}>'.format(self.body)

class Notification(db.Model):
    __tablename__ = 'notification'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))

    
class TimeStampedModel(object):
    created_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_time = db.Column(db.DateTime, onupdate=datetime.utcnow)

    class Meta:
        abstract = True

class AuthSMS(TimeStampedModel, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), name="휴대폰 번호", primary_key=False)
    auth_number = db.Column(db.Integer, name="인증번호")

    __tablename__ = 'authsms'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}

    def __init__(self, phone_number):
        self.phone_number = phone_number
        self.auth_number = randint(1000,10000)

    # def save(self, *args, **kwargs):
    #     self.auth_number = randint(1000,10000)
    #     #super().save(*args, **kwargs)
    #     self.send_sms()

    def send_sms(self):
        url = 'https://api-sens.ncloud.com/v1/sms/services/ncp:sms:kr:256998629750:mathmocha/messages/'
        data = {
            "type" : "SMS",
            "from" : "01051352116",
            "to" : [self.phone_number],
            "content" : "[테스트] 인증 번호 [{}]를 입력해주세요.".format(self.auth_number)
        }
        headers = {
            "Content-Type": "application/json",
            "x-ncp-auth-key": 'OJRMvmSyxZWS5MFdE2Tz',
            "x-ncp-service-secret": '34d55453eeec44ad855c0018ebf6e8d0'
            }

        requests.post(url, json=data, headers=headers)

    @classmethod
    def check_auth_number(cls, p_num, c_num):
        time_limit = datetime.utcnow() - timedelta(minutes=5)
        result = cls.query.filter_by(
            phone_number=p_num,
            auth_number=c_num).filter(
            cls.created_time.between(time_limit, datetime.utcnow()))
        print(result)
        if result:
            return True
        return False

        # if cls.created_time + timedelta(minutes=5) >= datetime.utcnow():
        #     if cls.auth_number == c_num:
        #         return True
        # else:
        #     return False

        # time_limit = datetime.utcnow() - timedelta(minutes=5)
        # result = cls.objects.filter(
        #     phone_number=p_num,
        #     auth_number=c_num,
        #     modified__gte=time_limit
        # )
        # if result:
        #     return True
        # return False


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Board(PaginatedAPIMixin, db.Model):
    __tablename__ = 'board'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    body = db.Column(db.String(5000))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)    
    filename = db.Column(db.String(1000))
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))    
    comments = db.relationship('Comment', backref='boards', lazy='dynamic')
    views = db.relationship('BoardView', backref='viewer', lazy='dynamic')

    def __repr__(self):
        return '<Board {}>'.format(self.title)
    
    def comment_counter(self):
        return Comment.query.filter(
            Comment.board_id == self.id
        ).count()
    
    def view_counter(self):
        return BoardView.query.filter(
            BoardView.board_id == self.id
        ).count()

class BoardView(db.Model):
    __tablename__ = 'board_view'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    board_id = db.Column(db.Integer, db.ForeignKey('board.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow) 


class Comment(PaginatedAPIMixin, db.Model):
    __tablename__ = 'comment'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(300))    
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow, index=True) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    board_id = db.Column(db.Integer, db.ForeignKey('board.id'))    
    def __repr__(self):
        return '<Comment {}, {}>'.format(self.board_id, self.id)


class Announce(PaginatedAPIMixin, db.Model):
    __tablename__ = 'announce'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    body = db.Column(db.String(1000))
    filename = db.Column(db.String(200))    
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    def __repr__(self):
        return '<Announce {}>'.format(self.id)