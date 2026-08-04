import logging
from flask import request, jsonify

from database import get_db
from models import usuario_model
from models.admin_model import execute_readonly_select
from validators.produto_validator import ValidationError
from validators.admin_query_validator import validate_readonly_select
from middlewares.error_handler import UnauthorizedError, ForbiddenError

logger = logging.getLogger(__name__)


def _require_admin():
    """Exige credenciais de usuário com tipo=admin (PB-3)."""
    dados = request.get_json(silent=True) or {}
    email = dados.get("email") or request.headers.get("X-Admin-Email")
    senha = dados.get("senha") or request.headers.get("X-Admin-Password")

    auth = request.authorization
    if auth and auth.username is not None:
        email = auth.username
        senha = auth.password

    if not email or not senha:
        raise UnauthorizedError(
            "Autenticação de admin obrigatória (Basic Auth ou email/senha)"
        )

    usuario = usuario_model.login_usuario(email, senha)
    if not usuario:
        raise UnauthorizedError("Credenciais inválidas")
    if usuario.get("tipo") != "admin":
        raise ForbiddenError("Acesso restrito a administradores")
    return usuario


def reset_database():
    _require_admin()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM usuarios")
    db.commit()
    logger.warning("Banco de dados resetado por admin autenticado")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query():
    """
    POST /admin/query — endpoint legado preservado com controles PB-3:
    autenticação admin + allowlist (somente SELECT em tabelas permitidas).
    """
    admin = _require_admin()
    dados = request.get_json(silent=True) or {}
    query = dados.get("sql", "")
    sql = validate_readonly_select(query)
    result = execute_readonly_select(sql)
    logger.info("Admin query por user_id=%s", admin.get("id"))
    return jsonify({"dados": result, "sucesso": True}), 200
