import logging
from flask import request, jsonify
import models
from validators.produto_validator import ValidationError
from middlewares.error_handler import NotFoundError, UnauthorizedError

logger = logging.getLogger(__name__)


def listar_usuarios():
    usuarios = models.get_todos_usuarios()
    return jsonify({"dados": usuarios, "sucesso": True}), 200


def buscar_usuario(id):
    usuario = models.get_usuario_por_id(id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar_usuario():
    dados = request.get_json()
    if not dados:
        raise ValidationError("Dados inválidos")

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")

    usuario_id = models.criar_usuario(nome, email, senha)
    logger.info("Usuário criado: %s", email)
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


def login():
    dados = request.get_json()
    if not dados:
        raise ValidationError("Dados inválidos")

    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")

    usuario = models.login_usuario(email, senha)
    if usuario:
        logger.info("Login bem-sucedido: %s", email)
        return jsonify({
            "dados": usuario,
            "sucesso": True,
            "mensagem": "Login OK",
        }), 200

    logger.info("Login falhou: %s", email)
    raise UnauthorizedError("Email ou senha inválidos")
