from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import ValidationError, DataRequired, Length
from app.models import User
from flask_wtf.file import FileField



class EditProfileForm(FlaskForm):
    username = StringField('사용자이름', validators=[DataRequired()])
    about_me = TextAreaField('본인 소개',
                             validators=[Length(min=0, max=140)])
    submit = SubmitField('수정')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('다른 이름을 사용해주세요.')


class PostForm(FlaskForm):
    post = TextAreaField('Say something', validators=[DataRequired()])
    submit = SubmitField('Submit')


class SearchForm(FlaskForm):
    q = StringField('Search', validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)

class MessageForm(FlaskForm):
    message = TextAreaField('Message', validators=[
        DataRequired(), Length(min=0, max=140)
    ])
    submit = SubmitField('Submit')

class BoardForm(FlaskForm):
    title = StringField('title', validators=[Length(min=1, max=100)])
    body = TextAreaField('Write anything', validators=[Length(min=1, max=5000)])
    filename = FileField('Your photo')
    submit = SubmitField('Done')

class CommentForm(FlaskForm):
    body = TextAreaField('Write your comment', validators=[Length(min=1, max=400)])
    submit = SubmitField('Done')

# class AuthForm(FlaskForm):
#     q = StringField('이메일 혹은 휴대폰 번호를 입력하세요.', validators=[DataRequired()])
    
#     def __init__(self, *args, **kwargs):
#         if 'formdata' not in kwargs:
#             kwargs['formdata'] = request.args
#         if 'csrf_enabled' not in kwargs:
#             kwargs['csrf_enabled'] = False
#         super(SearchForm, self).__init__(*args, **kwargs)