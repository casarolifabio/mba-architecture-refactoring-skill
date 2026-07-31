from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db


def _row_to_usuario_publico(row):
    """Serialização sem campo senha (não expor hash)."""
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def get_todos_usuarios():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios")
    return [_row_to_usuario_publico(row) for row in cursor.fetchall()]


def get_usuario_por_id(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?",
        (usuario_id,),
    )
    row = cursor.fetchone()
    return _row_to_usuario_publico(row) if row else None


def login_usuario(email, senha):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, nome, email, senha, tipo FROM usuarios WHERE email = ?",
        (email,),
    )
    row = cursor.fetchone()
    if row and check_password_hash(row["senha"], senha):
        return {
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "tipo": row["tipo"],
        }
    return None


def criar_usuario(nome, email, senha, tipo="cliente"):
    db = get_db()
    cursor = db.cursor()
    senha_hash = generate_password_hash(senha)
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    db.commit()
    return cursor.lastrowid
