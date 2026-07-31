import logging
from flask import request, jsonify
import models
from config.settings import STATUS_PEDIDO_VALIDOS
from validators.produto_validator import ValidationError

logger = logging.getLogger(__name__)


def criar_pedido():
    dados = request.get_json()
    if not dados:
        raise ValidationError("Dados inválidos")

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens or len(itens) == 0:
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    resultado = models.criar_pedido(usuario_id, itens)
    if "erro" in resultado:
        return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

    logger.info(
        "Pedido %s criado para usuario %s (notificações: email/sms/push)",
        resultado["pedido_id"],
        usuario_id,
    )

    return jsonify({
        "dados": resultado,
        "sucesso": True,
        "mensagem": "Pedido criado com sucesso",
    }), 201


def listar_pedidos_usuario(usuario_id):
    pedidos = models.get_pedidos_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_todos_pedidos():
    pedidos = models.get_todos_pedidos()
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    dados = request.get_json()
    if not dados:
        raise ValidationError("Dados inválidos")

    novo_status = dados.get("status", "")
    if novo_status not in STATUS_PEDIDO_VALIDOS:
        raise ValidationError("Status inválido")

    models.atualizar_status_pedido(pedido_id, novo_status)

    if novo_status == "aprovado":
        logger.info("NOTIFICAÇÃO: Pedido %s foi aprovado! Preparar envio.", pedido_id)
    if novo_status == "cancelado":
        logger.info(
            "NOTIFICAÇÃO: Pedido %s cancelado. Devolver estoque.",
            pedido_id,
        )

    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


def relatorio_vendas():
    relatorio = models.relatorio_vendas()
    return jsonify({"dados": relatorio, "sucesso": True}), 200
