from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

activity_units = db.Table('activity_units',
    db.Column('activity_id', db.Integer, db.ForeignKey('activity.id'), primary_key=True),
    db.Column('unit_id', db.Integer, db.ForeignKey('unit.id'), primary_key=True)
)

activity_categories = db.Table('activity_categories',
    db.Column('activity_id', db.Integer, db.ForeignKey('activity.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='scouter')
    activities = db.relationship('Activity', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    objectives = db.Column(db.Text, nullable=False)
    materials = db.Column(db.Text, nullable=True)
    environment = db.Column(db.String(20), nullable=False, default='indiferente')
    duration_range = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    units = db.relationship('Unit', secondary=activity_units, lazy='subquery',
                            backref=db.backref('activities', lazy=True))
    categories = db.relationship('Category', secondary=activity_categories, lazy='subquery',
                                 backref=db.backref('activities', lazy=True))

    def __repr__(self):
        return f'<Activity {self.title}>'


class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Unit {self.name}>'


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Category {self.name}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def seed_data():
    if Unit.query.count() == 0:
        units = [
            Unit(name='Castores', slug='castores'),
            Unit(name='Lobatos', slug='lobatos'),
            Unit(name='Scouts', slug='scouts'),
            Unit(name='Escultas', slug='escultas'),
            Unit(name='Rovers', slug='rovers'),
        ]
        db.session.add_all(units)

    if Category.query.count() == 0:
        categories = [
            Category(name='Acecho', slug='acecho'),
            Category(name='Velada', slug='velada'),
            Category(name='Taller', slug='taller'),
            Category(name='Gran Juego', slug='gran-juego'),
            Category(name='Dinámica de grupo', slug='dinamica-grupo'),
            Category(name='Juego de pistas', slug='juego-pistas'),
            Category(name='Actividad medioambiental', slug='medioambiental'),
            Category(name='Manualidad', slug='manualidad'),
        ]
        db.session.add_all(categories)

    if User.query.filter_by(role='admin').count() == 0:
        admin = User(username='admin', email='admin@scouts.es', role='admin')
        admin.set_password('admin1234')
        db.session.add(admin)

    db.session.commit()
