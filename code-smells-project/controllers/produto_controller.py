import logging
from flask import request, jsonify
import models
from validators.produto_validator import validate_produto_payload, ValidationError
from middlewares.error_handler import NotFoundError

logger = logging.getLogger(__name__)


def listar_produtos():
    produtos = models.get_todos_produtos()
    logger.info("Listando %s produtos", len(produtos))
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(id):
    produto = models.get_produto_por_id(id)
    if not produto:
        raise NotFoundError("Produto não encontrado")
    return jsonify({"dados": produto, "sucesso": True}), 200


def criar_produto():
    dados = request.get_json()
    payload = validate_produto_payload(dados, require_categoria_list=True)
    produto_id = models.criar_produto(
        payload["nome"],
        payload["descricao"],
        payload["preco"],
        payload["estoque"],
        payload["categoria"],
    )
    logger.info("Produto criado com ID: %s", produto_id)
    return jsonify({
        "dados": {"id": produto_id},
        "sucesso": True,
        "mensagem": "Produto criado",
    }), 201


def atualizar_produto(id):
    dados = request.get_json()
    produto_existente = models.get_produto_por_id(id)
    if not produto_existente:
        raise NotFoundError("Produto não encontrado")

    # Preserva comportamento legado do PUT: valida campos obrigatórios e
    # negativos, sem a lista estrita de categorias do POST (categoria livre).
    if not dados:
        raise ValidationError("Dados inválidos")
    if "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValidationError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValidationError("Estoque é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", "geral")

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")

    models.atualizar_produto(id, nome, descricao, preco, estoque, categoria)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id):
    produto = models.get_produto_por_id(id)
    if not produto:
        raise NotFoundError("Produto não encontrado")
    models.deletar_produto(id)
    logger.info("Produto %s deletado", id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = request.args.get("preco_min", None)
    preco_max = request.args.get("preco_max", None)

    if preco_min:
        preco_min = float(preco_min)
    if preco_max:
        preco_max = float(preco_max)

    resultados = models.buscar_produtos(termo, categoria, preco_min, preco_max)
    return jsonify({
        "dados": resultados,
        "total": len(resultados),
        "sucesso": True,
    }), 200
