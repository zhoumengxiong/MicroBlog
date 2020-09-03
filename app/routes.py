from flask import render_template, flash, redirect, url_for, request, g, current_app
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, ResetPasswordRequestForm, \
    ResetPasswordForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Post, ApprovalNo, WorkOrderNo, ProductCategory, ChipId
from werkzeug.urls import url_parse
from datetime import datetime
from app.email import send_api_mail
from app.forms import SearchForm


@app.before_request
def before_request():
    g.search_form = SearchForm()
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    # next_url = url_for(
    #     'index', page=posts.next_num) if posts.has_next else None
    # prev_url = url_for(
    #     'index', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Home', form=form, posts=posts.items, pagination=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# noinspection PyArgumentList
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    # next_url = url_for('user', username=user.username,
    #                    page=posts.next_num) if posts.has_next else None
    # prev_url = url_for('user', username=user.username,
    #                    page=posts.prev_num) if posts.has_prev else None
    return render_template('user.html', user=user, title='View Profile', posts=posts.items, pagination=posts)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)


@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You can not follow yourself!')
        redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You can not unfollow yourself!')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('user', username=username))


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    # next_url = url_for(
    #     'index', page=posts.next_num) if posts.has_next else None
    # prev_url = url_for(
    #     'index', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Explore', posts=posts.items, pagination=posts)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_api_mail(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/chipid_query', methods=['GET', 'POST'])
def chip_id():
    if request.method == "POST":
        field_query = request.form.get('field_query').upper().strip()
        product_category = request.form.getlist('product_category')
        method_query = request.form.get('method_query')
        return redirect(url_for("chipid_results", field_query=field_query, product_category=product_category,
                                method_query=method_query))
    return render_template('chipid_query.html', title="芯片ID查询入口")


@app.route('/chipid_results', methods=['GET', 'POST'])
def chipid_results():
    page = request.args.get('page', 1, type=int)
    field_query = request.args.get('field_query')
    product_category = request.args.getlist('product_category')
    method_query = request.args.get('method_query')
    if method_query == "1":
        pagination = db.session.query(ChipId).join(ApprovalNo).filter(
            ApprovalNo.approval_no == field_query).join(ProductCategory).filter(
            ProductCategory.product_category.in_(product_category)).paginate(
            page, app.config['POSTS_PER_PAGE'], False)
    else:
        pagination = db.session.query(ChipId).join(WorkOrderNo).filter(
            WorkOrderNo.work_order_no == field_query).join(ProductCategory).filter(
            ProductCategory.product_category.in_(product_category)).paginate(
            page, app.config['POSTS_PER_PAGE'], False)
    results = pagination.items
    # next_url = url_for(
    #     'chipid_results', field_query=field_query, product_category=product_category,
    #     method_query=method_query, page=pagination.next_num) if pagination.has_next else None
    # prev_url = url_for(
    #     'chipid_results', field_query=field_query, product_category=product_category,
    #     method_query=method_query, page=pagination.prev_num) if pagination.has_prev else None
    args = dict(field_query=field_query, product_category=product_category, method_query=method_query)
    return render_template('chipid_results.html', title='芯片ID查询结果', results=results, pagination=pagination, args=args)


@app.route('/search')
def search():
    if not g.search_form.validate():
        return redirect(url_for('explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    print(total)
    next_url = url_for('search', q=g.search_form.q.data, page=page + 1) if total['value'] > page * current_app.config[
        'POSTS_PER_PAGE'] else None
    prev_url = url_for('search', q=g.search_form.q.data, page=page - 1) if page > 1 else None
    return render_template('search.html', title='Search', posts=posts,
                           next_url=next_url, prev_url=prev_url)
