from flask import Flask
import os
from dotenv import load_dotenv

load_dotenv()


def create_app():
    app = Flask(__name__)

    # Database configuration
    database_url = os.getenv('DATABASE_URL', 'sqlite:///punctual.db')
    
    # Render PostgreSQL uses 'postgres://' but SQLAlchemy needs 'postgresql://'
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
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
