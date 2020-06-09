from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import ValidationError, DataRequired, Length
from app.models import User
from flask_wtf.file import FileField
from app.models import Source

class ElementaryFilterForm(FlaskForm):
    grade = SelectField('', 
                        choices=[(0, '학년'), 
                        (1, '3학년'),
                        (2, '4학년'),
                        (3, '5학년'),
                        (4, '6학년') ])
    semester = SelectField('', choices=[(0, '학기'),
                            (1, '1학기 중간'),
                            (2, '1학기 기말'),
                            (3, '2학기 중간'),
                            (4, '2학기 기말')])    
    submit = SubmitField(u'찾기')

class WriteButton(FlaskForm):
    submit = SubmitField('글쓰기')

class EditButton(FlaskForm):
    submit = SubmitField('수정')

class DeleteButton(FlaskForm):
    submit = SubmitField('삭제')

class WriteForm(FlaskForm):
    title = TextAreaField('제목', validators=[Length(min=1, max=100)])        
    body = TextAreaField('내용을 적어주세요.', render_kw={'class': 'form-control', 'rows': 8})
    filename = FileField('사진')
    submit = SubmitField('승인')

class CommentForm(FlaskForm):
    body = TextAreaField('댓글을 적어주세요.',
        validators=[Length(min=1, max=400)],
        render_kw={'rows': 3, 'cols': 1}) #'class': 'form-control',
    submit = SubmitField('댓글쓰기')


class SearchForm(FlaskForm):
    q = StringField('Search', validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)

    