class AppError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFoundError(AppError):
    def __init__(self, message="Recurso não encontrado"):
        super().__init__(message, 404)


class UnauthorizedError(AppError):
    def __init__(self, message="Não autorizado"):
        super().__init__(message, 401)


class ForbiddenError(AppError):
    def __init__(self, message="Proibido"):
        super().__init__(message, 403)


class ConflictError(AppError):
    def __init__(self, message="Conflito"):
        super().__init__(message, 409)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return {"error": err.message}, err.status_code

    @app.errorhandler(404)
    def handle_404(_err):
        return {"error": "Recurso não encontrado"}, 404

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        app.logger.exception("Erro não tratado: %s", err)
        return {"error": "Erro interno"}, 500
