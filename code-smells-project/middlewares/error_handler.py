import logging
from flask import jsonify
from validators.produto_validator import ValidationError

logger = logging.getLogger(__name__)


class NotFoundError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        self.status_code = 404


class UnauthorizedError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        self.status_code = 401


class ForbiddenError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        self.status_code = 403


def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation(err):
        return jsonify({"erro": err.message}), err.status_code

    @app.errorhandler(NotFoundError)
    def handle_not_found(err):
        return jsonify({"erro": err.message, "sucesso": False}), err.status_code

    @app.errorhandler(UnauthorizedError)
    def handle_unauthorized(err):
        return jsonify({"erro": err.message, "sucesso": False}), err.status_code

    @app.errorhandler(ForbiddenError)
    def handle_forbidden(err):
        return jsonify({"erro": err.message, "sucesso": False}), err.status_code

    @app.errorhandler(404)
    def handle_http_404(_err):
        return jsonify({"erro": "Recurso não encontrado", "sucesso": False}), 404

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("Erro não tratado: %s", err)
        return jsonify({"erro": str(err)}), 500
