from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from app import db
from app.main.forms import *
from app.models import User, Message, Source, Board, Question, GradeUp, \
    Comment, Comment_GradeUp, Comment_Problem, Comment_Question \
        , Customer, Announce
         #, Post, Notification, Board, Comment, Problem
from app.main import bp
from app.auth.forms import LoginForm
from sqlalchemy import desc, select, or_, join, union
from werkzeug import secure_filename
import os


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
#@login_required
def index():
    sources = Announce.query.order_by(desc('timestamp')).limit(3)
    return render_template('main.html', sources=sources)
    # if current_user.is_authenticated:    
    #     form = PostForm()
    #     if form.validate_on_submit():
    #         #language = guess_language(form.post.data)
    #         language = ''        
    #         if language == 'UNKNOWN' or len(language) > 5:
    #             language = ''
    #         post = Post(body=form.post.data, author=current_user,
    #                     language=language)
    #         db.session.add(post)
    #         db.session.commit()
    #         flash(_('Your post is now live!'))
    #         return redirect(url_for('main.index'))
    #     page = request.args.get('page', 1, type=int)
    #     posts = current_user.followed_posts().paginate(
    #         page, current_app.config['POSTS_PER_PAGE'], False)
    #     next_url = url_for('main.index', page=posts.next_num) \
    #         if posts.has_next else None
    #     prev_url = url_for('main.index', page=posts.prev_num) \
    #         if posts.has_prev else None
    #     return render_template('index.html', title=_('Home'), form=form,
    #                         posts=posts.items, next_url=next_url,
    #                         prev_url=prev_url)
    # else:
    #     return redirect(url_for('auth.login'))


# @bp.route('/explore')
# @login_required
# def explore():
#     page = request.args.get('page', 1, type=int)
#     posts = Post.query.order_by(Post.timestamp.desc()).paginate(
#         page, current_app.config['POSTS_PER_PAGE'], False)
#     next_url = url_for('main.explore', page=posts.next_num) \
#         if posts.has_next else None
#     prev_url = url_for('main.explore', page=posts.prev_num) \
#         if posts.has_prev else None
#     return render_template('index.html', title=_('Explore'),
#                            posts=posts.items, next_url=next_url,
#                            prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)

    boards = user.boards
    questions = user.questions
    gradeups = user.gradeups
    posts = boards.union(questions).union(gradeups)
    posts = posts.order_by(Board.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)

    comments_board = user.comments
    comments_question = user.comment_questions
    comments_gradeup = user.comment_gradeups
    commnets_problem = user.comment_problems

    comments = comments_board.union(comments_question).union(comments_gradeup).union(commnets_problem)
    comments = comments.order_by(Comment.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('main.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    
    next_url_comments = url_for('main.user', username=user.username,
                       page=comments.next_num) if comments.has_next else None
    prev_url_commnets = url_for('main.user', username=user.username,
                       page=comments.prev_num) if comments.has_prev else None

    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url,
                           comments=comments.items, next_url_comments=next_url_comments, prev_url_commnets=prev_url_commnets)


@bp.route('/ProfileUpdate', methods=['GET', 'POST'])
@login_required
def ProfileUpdate():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('quickform.html', title='프로필 수정',
                           form=form)


@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User %(username)s not found.', username=username)
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following %(username)s!', username=username)
    return redirect(url_for('main.user', username=username))


@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User %(username)s not found.', username=username)
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following %(username)s.', username=username)
    return redirect(url_for('main.user', username=username))


# @bp.route('/translate', methods=['POST'])
# @login_required
# def translate_text():
#     return jsonify({'text': translate(request.form['text'],
#                                       request.form['source_language'],
#                                       request.form['dest_language'])})

# @bp.before_app_request
# def before_request():
#     if current_user.is_authenticated:
#         current_user.last_seen = datetime.utcnow()
#         db.session.commit()
#         g.search_form = SearchForm()
#     g.locale = str(get_locale()) 

# elasticsearch 이용한 full-text search 
# 자료가 게시판 규모가 커지면 필요한 기능
# @bp.route('/search', methods=['GET', 'POST'])
# @login_required
# def search():
#     if not g.search_form.validate():
#         return redirect(url_for('main.explore'))
#     page = request.args.get('page', 1, type=int)
#     posts, total = Post.search(g.search_form.q.data, page, 
#                                current_app.config['POSTS_PER_PAGE'])
#     next_url = url_for('main.search', q=g.search_form.q.data, page= page+1) \
#     if total > page*current_app.config['POSTS_PER_PAGE'] else None
#     prev_url = url_for('main.search', q=g.search_form.q.data, page = page -1) \
#     if page > 1 else None
#     return render_template('search.html', title=_('Search'), posts=posts, 
#                            next_url=next_url, prev_url=prev_url)  

@bp.route('/search', methods=['GET', 'POST'])
@login_required
def search():    
    page = request.args.get('page', 1, type=int)
    if g.search_form.validate():
        posts = Board.query
        posts = posts.join(User).filter(or_(
            User.username.like('%'+g.search_form.q.data+'%'),
            Board.body.like('%'+g.search_form.q.data+'%')
            ))    
        # elif search_board == 'board':
        #     posts = Board.query
        #     posts = posts.join(User).filter(or_(
        #         User.username.like('%'+g.search_form.q.data+'%'),
        #         Board.title.like('%'+g.search_form.q.data+'%'),
        #         Board.body.like('%'+g.search_form.q.data+'%')
        #     ))

        
    posts = posts.order_by(Board.timestamp.desc()).all()
    total = len(posts)
    next_url = url_for('main.search', q=g.search_form.q.data, page= page+1) \
    if total > page*current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page = page -1) \
    if page > 1 else None           
        
    return render_template('search.html', title='Search', posts=posts,
    next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_popup.html', user=user)

@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
        body=form.message.data)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.add(msg)        
        db.session.commit()
        flash('쪽지를 전송했습니다..')
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title='보낸 쪽지',
    form=form, recipient=recipient)

@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)

# Notification 기능 당장 log 분석에 방해되니 나중에 active 시키자.
# @bp.route('/notifications')
# @login_required
# def notifications():
#     since = request.args.get('since', 0.0, type=float)
#     notifications = current_user.notifications.filter(
#         Notification.timestamp > since + 600000000000).order_by(Notification.timestamp.asc())
#     return jsonify([{
#         'name':n.name,
#         'data':n.get_data(),
#         'timestamp':n.timestamp        
#     } for n in notifications])

@bp.route('/export_posts')
@login_required
def export_posts():
    if current_user.get_task_in_progress('export_posts'):
        flash('An export task is currently in progress')
    else:
        current_user.launch_task('export_posts', 'Exporting posts...')
        db.session.commit()

    return redirect(url_for('main.user', username=current_user.username))


@bp.route('/board', methods=['GET', 'POST'])
@login_required
def board():
    page = request.args.get('page', 1, type=int)
    posts = Board.query.order_by(Board.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.board', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.board', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('board.html', title=_('Board'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)

@bp.route('/write', methods=['POST'])
@login_required
def write():
    form = BoardForm()
    if form.validate_on_submit():
        if form.filename.data == None:
            filename = ''
        else:
            filename = secure_filename(form.filename.data.filename)
            form.filename.data.save(current_app.config['UPLOAD_FOLDER']+filename)
        user = User.query.filter_by(username=current_user.username).first_or_404()        
        board = Board(author=current_user, title = form.title.data, body = form.body.data, filename = filename)
        db.session.add(board)
        db.session.commit()    
        return redirect(url_for('main.board'))
    return render_template('edit_profile.html', title=_('Write anything!'),
                           form=form, board = True)

@bp.route('/edit/<bdid>', methods=['GET', 'POST'])
@login_required
def board_edit(bdid):
    board = Board.query.filter_by(id=bdid).first_or_404()
    if current_user.username == board.author.username:
        form = BoardForm()
        if form.validate_on_submit():
            board.title = form.title.data
            board.body = form.body.data
            if form.filename.data == None:
                filename = board.filename
            else:
                filename = secure_filename(form.filename.data.filename)
                form.filename.data.save(current_app.config['UPLOAD_FOLDER']+filename)

            board.filename = filename
            db.session.commit()
            flash(_('Your changes have been saved'))
            return redirect(url_for('main.board'))
        elif request.method == 'GET':
            form.title.data = board.title
            form.body.data = board.body
            
        return render_template('edit_profile.html', title=_('Edit your article'), form=form)
    else:
        flash(_('Unauthorized Access'))
        return redirect(url_for('main.board'))
    
@bp.route('/delete/<bdid>', methods=['GET', 'POST'])
@login_required
def board_delete(bdid):
    board = Board.query.filter_by(id=bdid).first_or_404()
    if current_user.username == board.author.username:        
        form = BoardForm()
        db.session.delete(board)
        db.session.commit()
        flash(_('Your article have been deleted'))
        return redirect(url_for('main.board'))
    else:
        flash(_('Unauthorized Access'))
        return redirect(url_for('main.board'))

# @bp.route('/edit_profile', methods=['GET', 'POST'])
# @login_required
# def edit_profile():
#     form = EditProfileForm(current_user.username)
#     if form.validate_on_submit():
#         current_user.username = form.username.data
#         current_user.about_me = form.about_me.data
#         db.session.commit()
#         flash(_('Your changes have been saved.'))
#         return redirect(url_for('main.edit_profile'))
#     elif request.method == 'GET':
#         form.username.data = current_user.username
#         form.about_me.data = current_user.about_me
#     return render_template('edit_profile.html', title=_('Edit Profile'),
#                            form=form)

@bp.route('/board/<bdid>', methods=['POST', 'GET'])
@login_required
def content(bdid):
    bd = Board.query.filter_by(id=bdid).first_or_404()
    if bd.filename:
        file_image = current_app.config['UPLOAD_FOLDER']+'/'+ bd.filename
    else:
        file_image = None
    next_bd = Board.query.filter(bd.id < Board.id).first()
    prev_bd = Board.query.order_by(desc(Board.id)).filter(bd.id > Board.id).first()

    form = CommentForm()
    comments = Comment.query.filter_by(board_id=bd.id)

    if form.validate_on_submit():
        comment = Comment(body=form.body.data, author=current_user, board_id=bd.id)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment is now live!')
        return render_template('board_content.html', post=bd, next_bd=next_bd, 
    prev_bd=prev_bd, file_image=file_image, comments=comments, form=form)
    return render_template('board_content.html', post=bd, next_bd=next_bd, 
    prev_bd=prev_bd, file_image=file_image, comments=comments, form=form)

@bp.route('/faq/<category>', methods=['POST', 'GET'])
def faq(category):
    form = SelectFaq()    
    questions = Customer.query
    if form.validate_on_submit():
        questions = Customer.query.filter(Customer.category==form.category.data)
    page = request.args.get('page', 1, type=int)
    questions = questions.paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.faq', category=category, page=questions.next_num, form=form)\
        if questions.has_next else None
    prev_url = url_for('main.faq', category=category, page=questions.prev_num, form=form)\
        if questions.has_prev else None

    return render_template('faq.html', questions=questions.items, next_url=next_url, prev_url=prev_url, form=form)

@bp.route('/test', methods=['POST', 'GET'])
def test():
    if request.method['name'] == 'all':
        questions = Customer.query
    else:
        questions = Customer.query.filter(Customer.category==request.method['name'])
    page = request.args.get('page', 1, type=int)
    
    questions = questions.paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('main.faq',  page=questions.next_num)\
        if questions.has_next else None
    prev_url = url_for('main.faq', page=questions.prev_num)\
        if questions.has_prev else None

    return 'Hello, World!'
