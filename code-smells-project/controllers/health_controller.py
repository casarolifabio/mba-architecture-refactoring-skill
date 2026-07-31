from flask import jsonify, current_app
from database import get_db


def health_check():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT 1")
    cursor.execute("SELECT COUNT(*) FROM produtos")
    produtos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    usuarios = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM pedidos")
    pedidos = cursor.fetchone()[0]

    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": {
            "produtos": produtos,
            "usuarios": usuarios,
            "pedidos": pedidos,
        },
        "versao": "1.0.0",
        "ambiente": "desenvolvimento" if current_app.debug else "producao",
        "db_path": current_app.config["DATABASE"],
        "debug": current_app.debug,
    }), 200


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": "1.0.0",
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })
