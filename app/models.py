from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from flask_login import UserMixin
from app import login
from hashlib import md5
from time import time
import jwt
from app import app

followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
                     )


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
            followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


# 定义WorkOrderNo模型类
class WorkOrderNo(db.Model):
    __tablename__ = 'work_order_no'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    work_order_no = db.Column(db.String(15), unique=True, nullable=False, index=True)
    chipids = db.relationship("ChipId", back_populates="workorderno")


# 定义ApprovalNo模型类
class ApprovalNo(db.Model):
    __tablename__ = 'approval_no'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    approval_no = db.Column(db.String(12), unique=True, nullable=False, index=True)
    chipids = db.relationship("ChipId", back_populates="approvalno")


# 定义ProductCategory模型类
class ProductCategory(db.Model):
    __tablename__ = 'product_category'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_category = db.Column(db.String(20), unique=True,
                              nullable=False, index=True)
    chipids = db.relationship("ChipId", back_populates="productcategory")


# 定义ChipId模型类
class ChipId(db.Model):
    __tablename__ = 'chip_id'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chip_id = db.Column(db.String(48), unique=True, nullable=False)
    asset_no = db.Column(db.String(22), unique=True, nullable=False)
    work_order_no_id =db.Column(db.Integer, db.ForeignKey('work_order_no.id'))
    approval_no_id = db.Column(db.Integer, db.ForeignKey('approval_no.id'))
    product_category_id = db.Column(db.Integer, db.ForeignKey('product_category.id'))
    workorderno = db.relationship("WorkOrderNo", back_populates="chipids")
    approvalno = db.relationship("ApprovalNo", back_populates="chipids")
    productcategory = db.relationship("ProductCategory", back_populates="chipids")