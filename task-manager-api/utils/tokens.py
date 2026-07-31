from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from flask import current_app


def _serializer():
    return URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"],
        salt="task-manager-auth",
    )


def issue_access_token(user_id):
    """Token assinado (itsdangerous). Não é JWT; preserva o campo `token` no login."""
    return _serializer().dumps({"uid": user_id})


def verify_access_token(token, max_age=None):
    if max_age is None:
        max_age = current_app.config.get("TOKEN_MAX_AGE_SECONDS", 86400)
    try:
        data = _serializer().loads(token, max_age=max_age)
        return data.get("uid")
    except (BadSignature, SignatureExpired, TypeError, ValueError):
        return None
