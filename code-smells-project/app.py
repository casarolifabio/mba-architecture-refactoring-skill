import logging
from flask import Flask
from flask_cors import CORS

from config import settings
from database import get_db, close_db, init_db
from views.routes import register_routes
from middlewares.error_handler import register_error_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    app.config["DATABASE"] = settings.DATABASE

    CORS(app)
    app.teardown_appcontext(close_db)
    register_error_handlers(app)
    register_routes(app)
    init_db(app)
    return app


app = create_app()


if __name__ == "__main__":
    logging.getLogger(__name__).info(
        "SERVIDOR INICIADO em http://localhost:%s", settings.PORT
    )
    # load_dotenv=False evita falha se houver .env binário/inválido no cwd pai
    app.run(
        host=settings.HOST,
        port=settings.PORT,
        debug=settings.DEBUG,
        load_dotenv=False,
    )
