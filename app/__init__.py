import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask import render_template

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'warning'

ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'odt', 'rtf',
    'ppt', 'pptx', 'odp',
    'xls', 'xlsx', 'ods',
    'png', 'jpg', 'jpeg', 'gif', 'webp',
    'zip', 'rar', '7z',
    'txt', 'md',
}
MAX_FILE_MB = 20


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///scouts.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_MB * 1024 * 1024
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.admin.routes import admin_bp
    from app.community.routes import community_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(community_bp, url_prefix='/comunidad')

    with app.app_context():
        from app import models
        db.create_all()
        models.seed_data()
        
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403
    
    from app.main.routes import DURATIONS_DISPLAY

    @app.context_processor
    def inject_globals():
        return dict(durations_display=DURATIONS_DISPLAY)
    
    from app.main.routes import ENVIRONMENTS, DURATIONS_DISPLAY

    @app.context_processor
    def inject_globals():
        return dict(environments=ENVIRONMENTS, durations_display=DURATIONS_DISPLAY)

    return app
