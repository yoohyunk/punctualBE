from flask import Flask
import os
from dotenv import load_dotenv

load_dotenv()


def create_app():
    app = Flask(__name__)

    # 데이터베이스 설정 (SQLite)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'sqlite:///punctual.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # SQLAlchemy 초기화
    from .models import db
    db.init_app(app)

    # 블루프린트 등록
    from .routes import main_bp
    app.register_blueprint(main_bp)

    # 데이터베이스 테이블 생성 (개발 환경용)
    with app.app_context():
        db.create_all()

    return app
