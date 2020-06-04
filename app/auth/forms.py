from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, DateField, SelectField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('아이디', validators=[DataRequired()])
    password = PasswordField('비밀번호', validators=[DataRequired()])
    remember_me = BooleanField('아이디 저장')
    submit = SubmitField('로그인')
    
class RegistrationForm(FlaskForm):
    username = StringField('사용자 아이디', validators=[DataRequired()])
    birthday = DateField('생년월일', format='%Y-%m-%d', render_kw={"placeholder": "ex)2019-06-17"} )
    email = StringField('이메일', validators=[Email()])
    phone = StringField('휴대폰', validators=[DataRequired()])
    password = PasswordField('비밀번호', validators=[DataRequired()])
    password2 = PasswordField('비밀번호 확인', 
                              validators=[DataRequired(), EqualTo('password')])    
    submit = SubmitField('등록하기')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('다른 닉네임을 입력해주세요.')
        
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('사용중인 이메일입니다.')        

    def validate_phone(self, phone):
        user = User.query.filter_by(phone=phone.data).first()
        if user is not None:
            raise ValidationError('사용중인 휴대전화입니다.')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('본인 이메일주소를 입력해주세요.', validators=[DataRequired(), Email()])
    submit = SubmitField('비밀번호 초기화를 위한 이메일받기')

class RegisterRequestForm(FlaskForm):
    email = StringField('이메일', validators=[DataRequired(), Email()])
    submit = SubmitField('이메일 인증')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('비밀번호', validators=[DataRequired()])
    password2 = PasswordField(
        '다시 한번 입력해주세요.', validators=[DataRequired(), EqualTo('비밀번호')])
    submit = SubmitField('비밀번호 다시 설정하기')

class Type_Auth(FlaskForm):
    type_auth = SelectField(u'인증 방식을 선택하세요.',
    choices=[('email','email로 인증'), ('phone', '휴대폰으로 인증')])