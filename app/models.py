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

positions_users = db.Table('positions_users',
                    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                    db.Column('position_id', db.Integer(), db.ForeignKey('position.id')))

categories_sources = db.Table('categories_sources',
                    db.Column('source_id', db.Integer(), db.ForeignKey('source.id')),
                    db.Column('category_id', db.Integer(), db.ForeignKey('category.id')))



class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer(), primary_key=True)
    categories = db.Column(db.String(20), unique=True)
    categories_description = db.Column(db.String(20))    
    def __str__(self):
        return self.categories

grades_sources = db.Table('grades_sources',
                    db.Column('source_id', db.Integer(), db.ForeignKey('source.id')),
                    db.Column('grade_id', db.Integer(), db.ForeignKey('grade.id')))

class Grade(db.Model):
    __tablename__ = 'grade'
    id = db.Column(db.Integer(), primary_key=True)
    grade = db.Column(db.String(15), unique=True)
    grade_description = db.Column(db.String(10))
    school = db.Column(db.String(10))
    
    #sources = db.relationship('Source', secondary=grades_sources)
    def __str__(self):
        return self.grade_description

semesters_sources = db.Table('semesters_sources',
                    db.Column('source_id', db.Integer(), db.ForeignKey('source.id')),
                    db.Column('semester_id', db.Integer(), db.ForeignKey('semester.id')))

class Semester(db.Model):
    __tablename__ = 'semester'
    id = db.Column(db.Integer(), primary_key=True)
    semester = db.Column(db.String(10), unique=True)
    #sources = db.relationship('Source', secondary=semesters_sources)
    def __str__(self):
        return self.semester

textbooks_sources = db.Table('textbooks_sources',
                    db.Column('source_id', db.Integer(), db.ForeignKey('source.id')),
                    db.Column('textbook_id', db.Integer(), db.ForeignKey('textbook.id')))

class Textbook(db.Model):
    __tablename__ = 'textbook'
    id = db.Column(db.Integer(), primary_key=True)
    textbook = db.Column(db.String(10), unique=True)
    #sources = db.relationship('Source', secondary=category1_sources)
    def __str__(self):
        return self.textbook

class Position(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    positions = db.Column(db.String(10), unique=True)
    description = db.Column(db.String(20))
    users = db.relationship('User', secondary=positions_users, backref='users')
    def __str__(self):
        return self.positions

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
    
    positions = db.relationship('Position', secondary=positions_users,
                                backref='user', lazy='dynamic')
    sources = db.relationship('Source', backref='author', lazy='dynamic')
    boards = db.relationship('Board', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    gradeups = db.relationship('GradeUp', backref='author', lazy='dynamic')
    questions = db.relationship('Question', backref='author', lazy='dynamic')
    comment_questions = db.relationship('Comment_Question', backref='author', lazy='dynamic')
    comment_gradeups = db.relationship('Comment_GradeUp', backref='author', lazy='dynamic')
    comment_problems = db.relationship('Comment_Problem', backref='author', lazy='dynamic')
    grade_id = db.Column(db.Integer, db.ForeignKey('grade.id'))
    grades = db.relationship('Grade', backref='user')

    liked_source = db.relationship('SourceLike', foreign_keys='SourceLike.user_id', backref='user', lazy='dynamic')

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
    
    def like_source(self, post, type):
        try:
            school = post.school
        except:
            school = post.grades[0].school
        if not self.has_liked_source(post, type):
            like = SourceLike(user_id=self.id, source_id=post.id, type=type, school=school)
            db.session.add(like)

    def unlike_source(self, post, type):
        try:
            school = post.school
        except:
            school = post.grades[0].school
        if self.has_liked_source(post, type):
            SourceLike.query.filter(and_(
            SourceLike.user_id == self.id,
            SourceLike.source_id == post.id,
            SourceLike.type == type,
            SourceLike.school == school)
            ).delete()

    def has_liked_source(self, post, type):
        try:
            school = post.school
        except:
            school = post.grades[0].school
        return SourceLike.query.filter(and_(
            SourceLike.user_id == self.id,
            SourceLike.source_id == post.id,
            SourceLike.type == type,
            SourceLike.school == school)).count() > 0

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

class SourceLike(db.Model):
    __tablename__ = 'source_like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    source_id = db.Column(db.Integer)
    type = db.Column(db.String(20))
    school = db.Column(db.String(20))
    
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

class GradeUp(PaginatedAPIMixin, db.Model):
    __tablename__ = 'gradeup'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    # __searchable__ = ['title', 'body']

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    body = db.Column(db.String(5000))
    school = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)    
    filename = db.Column(db.String(1000))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comments = db.relationship('Comment_GradeUp', backref='gradeups', lazy='dynamic')
    views = db.relationship('GradeUpView', backref='viewer', lazy='dynamic')

    def __repr__(self):
        return '<GradeUp {}>'.format(self.title)

    def comment_counter(self):
        return Comment_GradeUp.query.filter(
        and_(Comment_GradeUp.board_id == self.id, Comment_GradeUp.school == self.school)
        ).count()

    def like_counter(self):
        return SourceLike.query.filter(and_(
        SourceLike.source_id == self.id,
        SourceLike.type == 'gardeup',
        SourceLike.school == self.school)).count() 

    def view_source(self, user):        
            if not self.has_viewed_source(user):
                view = GradeUpView(user_id=user.id, gradeup_id=self.id)
                db.session.add(view)

    def has_viewed_source(self, user):        
        return GradeUpView.query.filter(and_(
            GradeUpView.user_id == user.id,
            GradeUpView.gradeup_id == self.id
        )).count() > 0
    
    def view_counter(self):
        return GradeUpView.query.filter(
            GradeUpView.gradeup_id == self.id
        ).count()

class GradeUpView(db.Model):
    __tablename__ = 'gradeup_view'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    gradeup_id = db.Column(db.Integer, db.ForeignKey('gradeup.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow) 
    


class Comment_GradeUp(PaginatedAPIMixin, db.Model):
    __tablename__ = 'comment_gradeup'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(300))    
    school = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow, index=True) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    board_id = db.Column(db.Integer, db.ForeignKey('gradeup.id'))    
    def __repr__(self):
        return '<Comment_GradeUp {}, {}>'.format(self.gradeup_id, self.id)    
    


class Board(PaginatedAPIMixin, db.Model):
    __tablename__ = 'board'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    body = db.Column(db.String(5000))
    school = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)    
    filename = db.Column(db.String(1000))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comments = db.relationship('Comment', backref='boards', lazy='dynamic')
    views = db.relationship('BoardView', backref='viewer', lazy='dynamic')

    # likes = db.relationship('SourceLike',
    #                          primaryjoin=(Board.id == SourceLike.source_id),
    #                          backref='source', lazy='dyynamic')
    def __repr__(self):
        return '<Board {}>'.format(self.title)
    
    def comment_counter(self):
        return Comment.query.filter(
            and_(Comment.board_id == self.id, Comment.school == self.school)
        ).count()

    def like_counter(self):
        return SourceLike.query.filter(and_(
        SourceLike.source_id == self.id,
        SourceLike.type == 'board',
        SourceLike.school == self.school)).count()

    def view_source(self, user):        
            if not self.has_viewed_source(user):
                view = BoardView(user_id=user.id, board_id=self.id)
                db.session.add(view)

    def has_viewed_source(self, user):        
        return BoardView.query.filter(and_(
            BoardView.user_id == user.id,
            BoardView.board_id == self.id
        )).count() > 0
    
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
    school = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow, index=True) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    board_id = db.Column(db.Integer, db.ForeignKey('board.id'))    
    def __repr__(self):
        return '<Comment {}, {}>'.format(self.board_id, self.id)



class Question(PaginatedAPIMixin, db.Model):
    __tablename__ = 'question'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    # __searchable__ = ['title', 'body']

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    body = db.Column(db.String(5000))
    school = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)    
    filename = db.Column(db.String(1000))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comments = db.relationship('Comment_Question', backref='questions', lazy='dynamic')
    views = db.relationship('QuestionView', backref='viewer', lazy='dynamic')
    def __repr__(self):
        return '<Question {}>'.format(self.title)
    
    def comment_counter(self):
        return Comment_Question.query.filter(
        and_(Comment_Question.board_id == self.id, Comment_Question.school == self.school)
        ).count()

    def like_counter(self):
        return SourceLike.query.filter(and_(
        SourceLike.source_id == self.id,
        SourceLike.type == 'qna',
        SourceLike.school == self.school)).count()

    def view_source(self, user):        
        if not self.has_viewed_source(user):
            view = QuestionView(user_id=user.id, question_id=self.id)
            db.session.add(view)

    def has_viewed_source(self, user):        
        return QuestionView.query.filter(and_(
            QuestionView.user_id == user.id,
            QuestionView.question_id == self.id
        )).count() > 0
    
    def view_counter(self):
        return QuestionView.query.filter(
            QuestionView.question_id == self.id
        ).count()

class QuestionView(db.Model):
    __tablename__ = 'question_view'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow) 


class Comment_Question(PaginatedAPIMixin, db.Model):
    __tablename__ = 'comment_question'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(300))    
    school = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    board_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    def __repr__(self):
        return '<Comment_Question {}, {}>'.format(self.question_id, self.id)



class Source(PaginatedAPIMixin, db.Model):
    __tablename__ = 'source'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))        
    categories = db.relationship('Category', 
                            primaryjoin= (id == categories_sources.c.source_id),
                            secondary=categories_sources,                            
                            backref=db.backref('sources', lazy='dynamic'))
    grades = db.relationship('Grade',
                        primaryjoin= (id == grades_sources.c.source_id),
                        secondary=grades_sources,                       
                        backref=db.backref('sources', lazy='dynamic'))
    semesters = db.relationship('Semester',
                            primaryjoin= (id == semesters_sources.c.source_id),
                            secondary=semesters_sources,
                            backref=db.backref('sources', lazy='dynamic'))
    textbooks = db.relationship('Textbook', 
                            primaryjoin= (id == textbooks_sources.c.source_id),
                            secondary=textbooks_sources,                            
                            backref=db.backref('sources', lazy='dynamic'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    description = db.Column(db.String(200))
    filename = db.Column(db.String(100))
    comments = db.relationship('Comment_Problem', backref='boards', lazy='dynamic')
    views = db.relationship('SourceView', backref='viewer', lazy='dynamic')

    def __repr__(self):
        return '<Source {}>'.format(self.id)

    def like_counter(self):
        return SourceLike.query.filter(and_(
        SourceLike.source_id == self.id,
        SourceLike.type == self.categories[0].categories,
        SourceLike.school == self.grades[0].school)).count()

    def comment_counter(self):
        return Comment_Problem.query.filter(
        and_(Comment_Problem.board_id == self.id, Comment_Problem.school == self.grades[0].school)
        ).count()

    def view_source(self, user):        
        if not self.has_viewed_source(user):
            view = SourceView(user_id=user.id, source_id=self.id)
            db.session.add(view)

    def has_viewed_source(self, user):        
        return SourceView.query.filter(and_(
            SourceView.user_id == user.id,
            SourceView.source_id == self.id
        )).count() > 0
    
    def view_counter(self):
        return SourceView.query.filter(
            SourceView.source_id == self.id
        ).count()

class SourceView(db.Model):
    __tablename__ = 'source_view'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    source_id = db.Column(db.Integer, db.ForeignKey('source.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

class Comment_Problem(PaginatedAPIMixin, db.Model):
    __tablename__ = 'comment_problem'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(300))    
    school = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow, index=True) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    board_id = db.Column(db.Integer, db.ForeignKey('source.id'))
    def __repr__(self):
        return '<Comment_Problem {}, {}>'.format(self.board_id, self.id)

class Customer(PaginatedAPIMixin, db.Model):
    __tablename__ = 'customer'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    category = db.Column(db.String(10))
    body = db.Column(db.String(2000))
    filename = db.Column(db.String(1000))


    def __repr__(self):
        return '<Customer {}>'.format(self.id)

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