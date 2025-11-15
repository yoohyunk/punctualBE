from flask import Flask
import os
from dotenv import load_dotenv

load_dotenv()


def create_app():
    app = Flask(__name__)

    # Database configuration (SQLite)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'sqlite:///punctual.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize SQLAlchemy
    from .models import db
    db.init_app(app)

    # Register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)

    # Create database tables (for development)
    with app.app_context():
        db.create_all()

    return app
