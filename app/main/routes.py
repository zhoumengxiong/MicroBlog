from re import template
from flask import render_template, flash, redirect, url_for, request, g, current_app
from .. import db
from .forms import EditProfileForm, PostForm, SearchForm
from flask_login import current_user, login_required
from ..models import User, Post, ApprovalNo, WorkOrderNo, ProductCategory, ChipId
from datetime import datetime
from . import bp


@bp.before_request
def before_request():
    g.search_form = SearchForm()
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    # next_url = url_for(
    #     'index', page=posts.next_num) if posts.has_next else None
    # prev_url = url_for(
    #     'index', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Home', form=form, posts=posts.items, pagination=posts)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    # next_url = url_for('user', username=user.username,
    #                    page=posts.next_num) if posts.has_next else None
    # prev_url = url_for('user', username=user.username,
    #                    page=posts.prev_num) if posts.has_prev else None
    return render_template('user.html', user=user, title='View Profile', posts=posts.items, pagination=posts)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)


@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You can not follow yourself!')
        redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('main.user', username=username))


@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You can not unfollow yourself!')
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('main.user', username=username))


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    # next_url = url_for(
    #     'index', page=posts.next_num) if posts.has_next else None
    # prev_url = url_for(
    #     'index', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Explore', posts=posts.items, pagination=posts)


@bp.route('/chipid_query', methods=['GET', 'POST'])
def chip_id():
    if request.method == "POST":
        field_query = request.form.get('field_query').upper().strip()
        product_category = request.form.getlist('product_category')
        method_query = request.form.get('method_query')
        return redirect(url_for("main.chipid_results", field_query=field_query, product_category=product_category,
                                method_query=method_query))
    return render_template('chipid_query.html', title="芯片ID查询入口")


@bp.route('/chipid_results', methods=['GET', 'POST'])
def chipid_results():
    page = request.args.get('page', 1, type=int)
    field_query = request.args.get('field_query')
    product_category = request.args.getlist('product_category')
    method_query = request.args.get('method_query')
    if method_query == "1":
        pagination = db.session.query(ChipId).join(ApprovalNo).filter(
            ApprovalNo.approval_no == field_query).join(ProductCategory).filter(
            ProductCategory.product_category.in_(product_category)).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    else:
        pagination = db.session.query(ChipId).join(WorkOrderNo).filter(
            WorkOrderNo.work_order_no == field_query).join(ProductCategory).filter(
            ProductCategory.product_category.in_(product_category)).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    results = pagination.items
    # next_url = url_for(
    #     'chipid_results', field_query=field_query, product_category=product_category,
    #     method_query=method_query, page=pagination.next_num) if pagination.has_next else None
    # prev_url = url_for(
    #     'chipid_results', field_query=field_query, product_category=product_category,
    #     method_query=method_query, page=pagination.prev_num) if pagination.has_prev else None
    args = dict(field_query=field_query, product_category=product_category, method_query=method_query)
    return render_template('chipid_results.html', title='芯片ID查询结果', results=results, pagination=pagination, args=args)


@bp.route('/search')
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    print(total)
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) if total['value'] > page * \
                                                                                current_app.config[
                                                                                    'POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) if page > 1 else None
    return render_template('search.html', title='Search', posts=posts,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/resume_data_analysis')
def get_resume():
    phone_number = '15320810712'
    email = "zhoumengxiong@outlook.com"
    career_objective = "数据分析"
    return render_template('resume_data_analysis.html', phone_number=phone_number, email=email,
                           career_objective=career_objective)
