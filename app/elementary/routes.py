from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, jsonify, current_app, send_from_directory
from flask_login import current_user, login_required, login_user
from app import db
from app.auth.forms import LoginForm
from app.models import User, Source, Grade, Category, Semester,Board, Question, GradeUp,\
     Comment, Comment_GradeUp, Comment_Question, Comment_Problem, Announce
from app.elementary import bp
from app.elementary.forms import *
from sqlalchemy import desc, select, or_, join, and_
from werkzeug import secure_filename
import os, sqlalchemy
from sqlalchemy import create_engine, join, select
from sqlalchemy.sql import select
from sqlalchemy.orm import sessionmaker
from operator import itemgetter
from werkzeug.urls import url_parse
#engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])
Session = sessionmaker(bind=db)

# def type_collections(grade, type):
#     level = 'elementary'
#     if grade is None or '':
#         grade_description = ''
#     elif grade = 'third':
#         grade_description = '초등 3학년'
#     elif grade = 'fourth':   
#         grade_description = '초등 4학년'
#     elif grade = 'fifth':
#         grade_description = '초등 5학년'
#     elif grade = 'sixth':
#         grade_description = '초등 6학년'

#     if type is None:
#         type = ''
#     elif type == 'communication':
#         posts = Board
#         title = '초등 자유게시판'
#         comment_db = Comment

#     elif type == 'qna':
#         posts = Question
#         title = '초등 질문게시판'
#         comment_db = Comment_Question

#     elif type == 'gradeup':
#         posts = GradeUp
#         title = '성적이 올랐어요!'
#         comment_db = Comment_GradeUp
#     else:
#         posts = Source
#         comment_db = Comment_Problem
#         if type =='summary':
#             title = '요점 정리'
#         elif type == 'description':
#             title = '서술형 문제'
#         elif type == 'frequency':
#             title = '최다빈출문제'
#         elif type == 'incorrect':
#             title = '최다오답문제'
#         elif type == 'high_level':
#             title = '고난이도 문제'
#         elif type == 'calculation':
#             title = '계산력문제'
#         elif type == 'chapter':        
#             title = '단원별 문제'
#         elif type == 'concept':
#             title = '유형별 문제'    
# return (level=level, grade_description=grade_description, title, posts, comment_db)

@bp.route('/index/', methods=['GET', 'POST'])
def index():
    sources = Announce.query.order_by(desc('timestamp')).limit(3)
    if current_user.is_authenticated:
        form = SearchForm()
    else:
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user is None or not user.check_password(form.password.data):                      
                flash('아이디 혹은 비밀번호를 확인해주세요.')
                return redirect(url_for('auth.login'))
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('main.index', level='elementary')
            return redirect(next_page)
    return render_template('elementary/index.html', form=form, level='elementary', sources=sources)

@bp.route('/list/<type>/<grade>', methods=['GET', 'POST'])
def list(type, grade):
    form = LoginForm()
    form_filter = ElementaryFilterForm()   
  
    page = request.args.get('page', 1, type=int) 
    sources = Source.query.join(Semester, Source.semesters)\
        .join(Grade, Source.grades).join(Category, Source.categories).filter(Grade.school == '초등학교')
   
    if type == 'None':
        if len(grade) > 0:
            sources = sources.filter(Grade.grade == grade)
        else:
            sources = sources
    else:
        if len(grade) > 0:
            sources = sources.filter(Grade.grade == grade)\
                .filter(Category.categories == type)
                    
        else:
            sources = sources.filter(Category.categories == type)
   
    if form_filter.validate_on_submit():
        sources = Source.query.join(Semester, Source.semesters)\
        .join(Grade, Source.grades).join(Category, Source.categories).filter(Grade.school == '초등학교')

        grade = form_filter.grade.data
        semester = form_filter.semester.data

        print("====================================")
        print("====================================")
        print("====================================")
        print("====================================")
        print("====================================")
        print(grade, semester)
        print("====================================")
        print("====================================")
        print("====================================")
        print("====================================")
        
        if grade is not 0 and semester is not 0:
            flash('학년, 학기 중 적어도 하나를 입력 후 검색해주세요.')
            return

        if grade is not 0:
            if semester is not 0:
                sources = Source.query.filter(Grade.id == grade).filter(Semester.id == semester).order_by(Source.id.desc())
            else:
                sources = Source.query.filter(Grade.id == grade).order_by(Source.id.desc())

        else:
            if semester is not 0:
                sources = Source.query.filter(Grade.school == '초등학교').filter(Semester.id == semester).order_by(Source.id.desc())

            else:
                sources = Source.query.filter(Grade.school == '초등학교')

        # if search:
        #     sources = sources.query.filter(or_(
        #         Source.title.like('%'+search+'%'),
        #         Source.description.like('%'+search+'%')
        #     ))
        
        sources = sources.order_by(desc(Source.id)).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
        next_url = url_for('elementary.list', page=sources.next_num) if sources.has_next else None
        prev_url = url_for('elementary.list', page=sources.prev_num) if sources.has_prev else None
        return render_template('elementary/list.html', form=form, form_filter=form_filter, sources=sources.items, grade=grade, type=type, level='elementary')

    sources = sources.order_by(Source.timestamp.desc()).filter(Grade.grade == grade).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)    
    next_url = url_for('elementary.list', page=sources.next_num, grade=grade, type=type) \
        if sources.has_next else None
    prev_url = url_for('elementary.list', page=sources.prev_num, grade=grade, type=type) \
        if sources.has_prev else None
    return render_template('elementary/list.html', form=form, form_filter=form_filter,
                        sources=sources.items, grade=grade, type=type, level='elementary',
                        next_url=next_url, prev_url=prev_url)



@bp.route('/community/<type>', methods=['GET', 'POST'])
def community(type):
    Button = WriteButton()
    if Button.validate_on_submit():
        return redirect(url_for('elementary.writing', type=type))
    if type == 'communication':
        posts = Board
        title = '초등학생 자유게시판'
        comment_db = Comment
    elif type == 'qna':
        posts = Question
        title = '초등학생 질문게시판'
        comment_db = Comment_Question
    elif type == 'gradeup':
        posts = GradeUp
        title = '성적이 올랐어요!'
        comment_db = Comment_Question        
    
    
    page = request.args.get('page', 1, type=int)
    posts = posts.query.order_by(posts.id.desc())
    
    # .paginate(page, current_app['POSTS_PER_PAGE'], False)

    # next_url = url_for('elementary.community', page=posts.next_num, type=type) \
    #     if posts.has_next else None
    # prev_url = url_for('elementary.community', page=posts.prev_num, type=type) \
    #     if posts.has_prev else None
    return render_template('elementary/board.html', title=title, type=type, 
            posts=posts, form=Button, level='elementary')
            # , next_url=next_url, prev_url=prev_url)

@bp.route('/writing/<type>', methods=['GET', 'POST'])
@login_required
def writing(type):
    form = WriteForm()
    if type == 'communication':
        posts = Board
        title = '초등 자유게시판'
    elif type == 'qna':
        posts = Question
        title = '초등 질문게시판'
    elif type == 'gradeup':
        posts = GradeUp
        title = '성적이 올랐어요!'
    if form.validate_on_submit():
        if form.filename.data is None:
            filename = ''
        else:
            form.filename.data.save(current_app.config['UPLOAD_FOLDER']+form.filename.data.filename)
            filename = form.filename.data.filename 
        
        post = posts(author=current_user, title=form.title.data, body=form.body.data, filename=filename
                , school='초등학교')
        db.session.add(post)
        db.session.commit()    
        return redirect(url_for('elementary.community', type=type, level='elementary'))
    return render_template('/elementary/edit.html', form=form, type=type, title=title, level='elementary')

@bp.route('/contents/<type>/<postid>', methods=['POST', 'GET'])
@login_required
def content(postid, type):
    if type == 'communication':
        posts = Board
        title = '초등 자유게시판'
        comment_db = Comment

    elif type == 'qna':
        posts = Question
        title = '초등 질문게시판'
        comment_db = Comment_Question

    elif type == 'gradeup':
        posts = GradeUp
        title = '성적이 올랐어요!'
        comment_db = Comment_GradeUp

    else:
        posts = Source
        comment_db = Comment_Problem
        if type =='summary':
            title = '요점 정리'
        elif type == 'description':
            title = '서술형 문제'
        elif type == 'frequency':
            title = '최다빈출문제'
        elif type == 'incorrect':
            title = '최다오답문제'
        elif type == 'high_level':
            title = '고난이도 문제'
        elif type == 'calculation':
            title = '계산력문제'
        elif type == 'chapter':        
            title = '단원별 문제'
        elif type == 'concept':
            title = '유형별 문제'        
        
    post = posts.query.filter_by(id=postid).first_or_404()
    if not post.has_viewed_source(current_user):
        post.view_source(current_user)
        db.session.commit()
    
    try:
        grade = post.grades[0].grade
    except:
        grade = None

    if post.filename:
        file_image = current_app.config['UPLOAD_FOLDER']+'/'+ post.filename
    else:
        file_image = None
    next_post = posts.query.filter(post.id < posts.id).first()
    prev_post = posts.query.order_by(desc(posts.id)).filter(post.id > posts.id).first()
    
    form = CommentForm()
    button_edit = EditButton()
    button_delete = DeleteButton()
    comments = comment_db.query.filter(comment_db.board_id == postid)
    if form.validate_on_submit():
        comment = comment_db(body=form.body.data, author=current_user, board_id=postid, school='초등학교')
        db.session.add(comment)
        db.session.commit()
        flash('댓글이 등록되었습니다!')
        return redirect(url_for('elementary.content', postid=post.id, type=type, school='초등학교'))
    if button_edit.validate_on_submit():
        return redirect(url_for('elementary.editcontent', type=type, postid=postid, level='elementary'))
    if button_delete.validate_on_submit():
        return redirect(url_for('elementary.deletecontent', type=type, postid=postid, level='elementary'))
    return render_template('elementary/content.html', post=post, next_post=next_post, 
            prev_post=prev_post, file_image=file_image, type=type, school='초등학교',
            comments=comments, form=form, button_edit = button_edit, button_delete = button_delete, level='elementary', grade=grade)

@bp.route('/EditContent/<type>/<postid>', methods=['GET', 'POST'])
@login_required
def editcontent(postid, type):
    if type == 'communication':
        posts = Board
        title = '초등 자유게시판'
        comment_db = Comment

    elif type == 'qna':
        posts = Question
        title = '초등 질문게시판'
        comment_db = Comment_Question

    elif type == 'gradeup':
        posts = GradeUp
        title = '성적이 올랐어요!'
        comment_db = Comment_GradeUp

    else:
        posts = Source
        comment_db = Comment_Problem
        if type =='summary':
            title = '요점 정리'
        elif type == 'description':
            title = '서술형 문제'
        elif type == 'frequency':
            title = '최다빈출문제'
        elif type == 'incorrect':
            title = '최다오답문제'
        elif type == 'high_level':
            title = '고난이도 문제'
        elif type == 'calculation':
            title = '계산력문제'
        elif type == 'chapter':        
            title = '단원별 문제'
        elif type == 'concept':
            title = '유형별 문제'    
        

    post = posts.query.filter(posts.id == postid).first_or_404()    
    if current_user.username is not post.author.username:            
        flash('권한이 없습니다.')
        return redirect(url_for('elementary.community', type=type, level='elementary'))
    else:                   
        form = WriteForm()
        if form.validate_on_submit():                    
            post.title = form.title.data
            post.body = form.body.data
            if form.filename.data == '':
                filename = post.filename
            else:
                filename = secure_filename(form.filename.data.filename)
                form.filename.data.save(current_app.config['UPLOAD_FOLDER']+filename)
            post.filename = filename            
            db.session.commit()
            flash('수정이 완료되었습니다.')
            return redirect(url_for('elementary.community', type=type))
        elif request.method == 'GET':
            form.title.data = post.title
            form.body.data = post.body
        return render_template('/elementary/edit.html', form=form, type=type, title=title, level='elementary')
    

@bp.route('/DeleteContent/<type>/<postid>', methods=['GET', 'POST'])
@login_required
def deletecontent(postid, type):
    if type == 'communication':
        posts = Board
        title = '초등 자유게시판'
        comment_db = Comment

    elif type == 'qna':
        posts = Question
        title = '초등 질문게시판'
        comment_db = Comment_Question

    elif type == 'gradeup':
        posts = GradeUp
        title = '성적이 올랐어요!'
        comment_db = Comment_GradeUp

    else:
        posts = Source
        comment_db = Comment_Problem
        if type =='summary':
            title = '요점 정리'
        elif type == 'description':
            title = '서술형 문제'
        elif type == 'frequency':
            title = '최다빈출문제'
        elif type == 'incorrect':
            title = '최다오답문제'
        elif type == 'high_level':
            title = '고난이도 문제'
        elif type == 'calculation':
            title = '계산력문제'
        elif type == 'chapter':        
            title = '단원별 문제'
        elif type == 'concept':
            title = '유형별 문제'    
     
    post = posts.query.filter_by(id=postid).first_or_404()
    
    if current_user.username == post.author.username:        
        db.session.delete(post)
        db.session.commit()
        flash('게시글이 삭제되었습니다.')
        return redirect(url_for('elementary.community', type=type, level='elementary'))
    else:
        flash('권한이 없습니다.')
        return redirect(url_for('elementary.community', type=type, level='elementary'))

@bp.route('DownLoadContent/<path:filename>', methods=['GET'])
@login_required
def download(filename):
    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(directory=upload_folder,
                            filename=filename,
                            as_attachment=True)

@bp.route('like/<type>/<post_id>/<action>', methods=['POST', 'GET'])
@login_required
def sourcelike(post_id, type, action):
    if type == 'communication':
        posts = Board
        title = '초등 자유게시판'
        comment_db = Comment

    elif type == 'qna':
        posts = Question
        title = '초등 질문게시판'
        comment_db = Comment_Question

    elif type == 'gradeup':
        posts = GradeUp
        title = '성적이 올랐어요!'
        comment_db = Comment_GradeUp

    else:
        posts = Source
        comment_db = Comment_Problem
        if type =='summary':
            title = '요점 정리'
        elif type == 'description':
            title = '서술형 문제'
        elif type == 'frequency':
            title = '최다빈출문제'
        elif type == 'incorrect':
            title = '최다오답문제'
        elif type == 'high_level':
            title = '고난이도 문제'
        elif type == 'calculation':
            title = '계산력문제'
        elif type == 'chapter':        
            title = '단원별 문제'
        elif type == 'concept':
            title = '유형별 문제'    

    post = posts.query.filter_by(id=post_id).first_or_404()
    if action == 'like':
        current_user.like_source(post, type=type)
        db.session.commit()
    if action == 'unlike':
        current_user.unlike_source(post, type=type)
        db.session.commit()
    return redirect(request.referrer)

@bp.route('test', methods=['POST', 'GET'])
def test():
    type ='communication'
    Button = WriteButton()
    if Button.validate_on_submit():
        return redirect(url_for('elementary.writing', type=type))
    if type == 'communication':
        posts = Board
        title = '초등학생 자유게시판'
        comment_db = Comment
    elif type == 'qna':
        posts = Question
        title = '초등학생 질문게시판'
        comment_db = Comment_Question
    elif type == 'gradeup':
        posts = GradeUp
        title = '성적이 올랐어요!'
        comment_db = Comment_GradeUp
    print(posts, comment_db) 
    posts = posts.query.order_by(posts.id.desc())
    for post in posts:
        print(post)

    page = request.args.get('page', 1, type=int)
    posts = posts.paginate(page, current_app['POSTS_PER_PAGE'], False)
    # for post in posts.items:
    #     print(post)
    
    # next_url = url_for('elementary.community', page=posts.next_num, type=type) \
    #     if posts.has_next else None
    # prev_url = url_for('elementary.community', page=posts.prev_num, type=type) \
    #     if posts.has_prev else None
    return 'Hello, World!'