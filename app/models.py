import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

VALID_DURATIONS = ['less_30m', '30_60m', '1_2h', '2_4h', 'more_4h', 'multiple_days']

activity_units = db.Table('activity_units',
    db.Column('activity_id', db.Integer, db.ForeignKey('activity.id'), primary_key=True),
    db.Column('unit_id', db.Integer, db.ForeignKey('unit.id'), primary_key=True)
)

activity_categories = db.Table('activity_categories',
    db.Column('activity_id', db.Integer, db.ForeignKey('activity.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
)

activity_likes = db.Table('activity_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('activity_id', db.Integer, db.ForeignKey('activity.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

list_activities = db.Table('list_activities',
    db.Column('list_id', db.Integer, db.ForeignKey('custom_list.id'), primary_key=True),
    db.Column('activity_id', db.Integer, db.ForeignKey('activity.id'), primary_key=True),
    db.Column('added_at', db.DateTime, default=datetime.utcnow)
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='scouter')
    grupo_scout = db.Column(db.String(120), nullable=True)
    social_media = db.Column(db.JSON, nullable=True)

    def get_social(self, network):
        if not self.social_media:
            return None
        return self.social_media.get(network) or None

    activities = db.relationship('Activity', backref='author', lazy='dynamic',
                                 foreign_keys='Activity.user_id')
    liked_activities = db.relationship('Activity', secondary=activity_likes,
                                       lazy='dynamic',
                                       backref=db.backref('liked_by', lazy='dynamic'))
    custom_lists = db.relationship('CustomList', backref='owner', lazy='dynamic',
                                   cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def has_liked(self, activity):
        return self.liked_activities.filter(
            activity_likes.c.activity_id == activity.id
        ).count() > 0

    def __repr__(self):
        return f'<User {self.username}>'


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    objectives = db.Column(db.Text, nullable=False)
    materials = db.Column(db.Text, nullable=True)

    environment = db.Column(db.String(30), nullable=False, default='indiferente')
    location_detail = db.Column(db.String(120), nullable=True)

    duration_range = db.Column(db.String(20), nullable=False)
    min_participants = db.Column(db.Integer, nullable=True)
    max_participants = db.Column(db.Integer, nullable=True)

    attachment_filename = db.Column(db.String(260), nullable=True)
    attachment_original_name = db.Column(db.String(260), nullable=True)
    attachment_mime = db.Column(db.String(100), nullable=True)
    file_path = db.Column(db.String(512), nullable=True)

    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    units = db.relationship('Unit', secondary=activity_units, lazy='subquery',
                            backref=db.backref('activities', lazy=True))
    categories = db.relationship('Category', secondary=activity_categories, lazy='subquery',
                                 backref=db.backref('activities', lazy=True))

    @property
    def likes_count(self):
        return self.liked_by.count()

    @property
    def attachment_icon(self):
        if not self.attachment_mime:
            return '📎'
        if 'pdf' in self.attachment_mime:
            return '📄'
        if 'word' in self.attachment_mime or 'document' in self.attachment_mime:
            return '📝'
        if 'presentation' in self.attachment_mime or 'powerpoint' in self.attachment_mime:
            return '📊'
        if self.attachment_mime.startswith('image/'):
            return '🖼️'
        if 'zip' in self.attachment_mime or 'compressed' in self.attachment_mime:
            return '🗜️'
        return '📎'

    @property
    def participants_display(self):
        if self.min_participants and self.max_participants:
            return f'{self.min_participants}–{self.max_participants} participantes'
        if self.min_participants:
            return f'Mín. {self.min_participants} participantes'
        if self.max_participants:
            return f'Máx. {self.max_participants} participantes'
        return None

    def __repr__(self):
        return f'<Activity {self.title}>'


class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    order = db.Column(db.Integer, nullable=False, default=99)

    def __repr__(self):
        return f'<Unit {self.name}>'


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Category {self.name}>'


class CustomList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    is_public = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    activities = db.relationship('Activity', secondary=list_activities,
                                 lazy='dynamic',
                                 backref=db.backref('in_lists', lazy='dynamic'))

    def __repr__(self):
        return f'<CustomList {self.name}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def seed_data():
    if Unit.query.count() == 0:
        units = [
            Unit(name='Castores',     slug='castores',    order=1),
            Unit(name='Manada',       slug='manada',      order=2),
            Unit(name='Tropa Scout',  slug='tropa-scout', order=3),
            Unit(name='Escultas',     slug='escultas',    order=4),
            Unit(name='Clan Rover',   slug='clan-rover',  order=5),
        ]
        db.session.add_all(units)
    else:
        _migrate_units()

    if Category.query.count() == 0:
        categories = [
            Category(name='Acecho',                    slug='acecho'),
            Category(name='Velada',                    slug='velada'),
            Category(name='Taller',                    slug='taller'),
            Category(name='Gran Juego',                slug='gran-juego'),
            Category(name='Dinámica de grupo',         slug='dinamica-grupo'),
            Category(name='Juego de pistas',           slug='juego-pistas'),
            Category(name='Actividad medioambiental',  slug='medioambiental'),
            Category(name='Manualidad',                slug='manualidad'),
        ]
        db.session.add_all(categories)

    if User.query.filter_by(role='admin').count() == 0:
        admin = User(username='admin', email='admin@scouts.es', role='admin')
        admin.set_password('admin1234')
        db.session.add(admin)

    db.session.commit()


def _migrate_units():
    rename_map = {
        'Lobatos': ('Manada',      'manada',      2),
        'Scouts':  ('Tropa Scout', 'tropa-scout', 3),
        'Rovers':  ('Clan Rover',  'clan-rover',  5),
    }
    order_map = {
        'Castores':    1,
        'Escultas':    4,
    }
    changed = False
    for unit in Unit.query.all():
        if unit.name in rename_map:
            new_name, new_slug, new_order = rename_map[unit.name]
            unit.name  = new_name
            unit.slug  = new_slug
            unit.order = new_order
            changed = True
        elif unit.name in order_map and unit.order != order_map[unit.name]:
            unit.order = order_map[unit.name]
            changed = True
        elif unit.order == 99:
            unit.order = 99
            changed = True
    if changed:
        db.session.flush()
