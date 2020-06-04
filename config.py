import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    'mysql+pymysql://root:3141@localhost/profile_test_db?charset=utf8'
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MYSQL_DATABASE_USER = 'root'
    MYSQL_DATABASE_PASSWORD = '3141'
    MYSQL_DATABASE_DB = 'profile_test_db'
    MYSQL_DATABASE_HOST = 'localhost'
    
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    #     'sqlite:///' + os.path.join(basedir, 'app.db')
    # SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.googlemail.com'   #os.environ.get('MAIL_SERVER')
    MAIL_PORT = 465 #587 #int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = False    #os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'arkenkjs'    #os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = 'zippo0519.!'    #os.environ.get('MAIL_PASSWORD')
    ADMINS = ['arkenkjs@gmail.com']

    POSTS_PER_PAGE = 10
    LANGUAGES = ['en', 'ko']
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
    # 상대위치로 바꾸자.
    UPLOAD_FOLDER = "D:/web_work/mathmocha/app/static/uploads/"
    
    FLASK_ADMIN_SWATCH = 'cerulean'

    # Set config values for Flask-Security.
    # We're using PBKDF2 with salt.
    # SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'
    # SECURITY_PASSWORD_SALT = 'mathmocha'
    # SECURITY_EMAIL_SENDER = 'mathmocha732@gmail.com'