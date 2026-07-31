import logging
from flask import request, jsonify
from database import get_db
from validators.produto_validator import ValidationError

logger = logging.getLogger(__name__)


def reset_database():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM usuarios")
    db.commit()
    logger.warning("Banco de dados resetado")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query():
    """Preserva o endpoint legado POST /admin/query (SQL arbitrário)."""
    dados = request.get_json()
    if not dados:
        raise ValidationError("Dados inválidos")

    query = dados.get("sql", "")
    if not query:
        raise ValidationError("Query não informada")

    db = get_db()
    cursor = db.cursor()
    cursor.execute(query)
    if query.strip().upper().startswith("SELECT"):
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        return jsonify({"dados": result, "sucesso": True}), 200

    db.commit()
    return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
