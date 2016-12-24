from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import db
from flask import current_app, request
from flask_login import AnonymousUserMixin, UserMixin
from . import login_manager


class Permission:
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][1]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    avatar_hash = db.Column(db.String(32))

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can(self, permissions):
        return self.role is not None and \
                (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://gravatar.com/avatar'
            hash = self.avatar_hash or hashlib.md5(
                self.email.encode('utf-8')).hexdigest()
            return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
                url=url, hash=hash, size=size, default=default, rating=rating)

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


news_players = db.Table('news_players', db.Column('news_id',
                        db.Integer, db.ForeignKey('news.id')),
                        db.Column('player_id', db.Integer,
                                  db.ForeignKey('players.id')))


class Player(db.Model):
    __tablename__ = 'players'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    introduction = db.Column(db.Text)
    image = db.Column(db.String(128))
    news = db.relationship('News',
                           secondary=news_players,
                           back_populates='related_players',
                           lazy='dynamic')

    @staticmethod
    def generate_fake(count=100):
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            p = Player(name=forgery_py.name.full_name(),
                       introduction=forgery_py.lorem_ipsum.sentence())
        db.session.add(p)

    def __repr__(self):
        return '<Player %r>' % self.name

news_teams = db.Table('news_teams', db.Column('news_id',
                      db.Integer, db.ForeignKey('news.id')),
                      db.Column('team_id', db.Integer,
                                db.ForeignKey('teams.id')))


class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    introduction = db.Column(db.Text)
    players = db.relationship('Player', backref='team', lazy='dynamic')
    image = db.Column(db.String(128))
    news = db.relationship('News',
                           secondary=news_teams,
                           back_populates='related_teams',
                           lazy='dynamic')

    @staticmethod
    def generate_fake(count=100):
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            t = Team(name=forgery_py.name.full_name(),
                     introduction=forgery_py.lorem_ipsum.sentence())
            db.session.add(t)
            db.session.commit()

    def __repr__(self):
        return '<Team %r>' % self.name


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    news_id = db.Column(db.Integer, db.ForeignKey('news.id'))

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        news_count = News.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            n = News.query.offset(randint(0, news_count - 1)).first()
            c = Comment(body=forgery_py.lorem_ipsum.sentences(randint(1, 5)),
                        timestamp=forgery_py.date.date(True),
                        author=u, news=n)
            db.session.add(c)
            db.session.commit()

    def __repr__(self):
        return '<Comment %r>' % self.body


class News(db.Model):
    __tablename__ = 'news'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    content = db.Column(db.Text)
    image = db.Column(db.String(128))
    related_players = db.relationship('Player',
                                      secondary=news_players,
                                      back_populates='news',
                                      lazy='dynamic')
    related_teams = db.relationship('Team',
                                    secondary=news_teams,
                                    back_populates='news',
                                    lazy='dynamic')
    original_source = db.Column(db.String(128))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='news', lazy='dynamic')

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        player_count = Player.query.count()
        team_count = Team.query.count()
        for i in range(count):
            p = Player.query.offset(randint(0, player_count - 1)).first()
            t = Team.query.offset(randint(0, team_count - 1)).first()
            n = News(content=forgery_py.lorem_ipsum.sentences(randint(10, 20)),
                     title=forgery_py.lorem_ipsum.sentences(1),
                     timestamp=forgery_py.date.date(True),
                     image='500x300.png')
            n.related_players.append(p)
            n.related_teams.append(t)
            db.session.add(n)
            db.session.commit()

    def __repr__(self):
        return '<News %r>' % self.title
