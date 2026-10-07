import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()


def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object('app.config.Config')

    # Ensure upload subdirectories exist
    for subdir in ['qr', 'docs', 'observations', 'certificates']:
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], subdir), exist_ok=True)

    # Extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "null"  # file:// protocol for direct browser open
    ]}}, supports_credentials=True)

    # Serve uploaded files
    from flask import send_from_directory
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.instruments import instruments_bp
    from app.routes.applications import applications_bp
    from app.routes.certificates import certificates_bp
    from app.routes.admin import admin_bp
    from app.routes.notifications import notifications_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(instruments_bp, url_prefix='/api')
    app.register_blueprint(applications_bp, url_prefix='/api')
    app.register_blueprint(certificates_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(notifications_bp, url_prefix='/api')

    return app
