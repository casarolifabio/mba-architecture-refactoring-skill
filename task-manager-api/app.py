import logging
from flask import Flask
from flask_cors import CORS
from database import db
from config import settings
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp
from middlewares.error_handler import register_error_handlers
from utils.timeutils import utc_now
import models  # noqa: F401 — registra models no metadata

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = settings.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['TOKEN_MAX_AGE_SECONDS'] = settings.TOKEN_MAX_AGE_SECONDS

    CORS(app)
    db.init_app(app)
    register_error_handlers(app)

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(utc_now())}

    @app.route('/')
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == '__main__':
    app.run(
        debug=settings.DEBUG,
        host=settings.HOST,
        port=settings.PORT,
        load_dotenv=False,
    )
