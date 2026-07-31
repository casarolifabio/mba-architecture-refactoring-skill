import logging
from database import db
from models.user import User
from models.task import Task
from middlewares.error_handler import (
    AppError,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    ConflictError,
)
from validators.schemas import validate_create_user, validate_login
from utils.tokens import issue_access_token
from utils.helpers import VALID_ROLES, MIN_PASSWORD_LENGTH
import re

logger = logging.getLogger(__name__)
_EMAIL_RE = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')


def list_users():
    users = User.query.all()
    result = []
    for u in users:
        result.append({
            'id': u.id,
            'name': u.name,
            'email': u.email,
            'role': u.role,
            'active': u.active,
            'created_at': str(u.created_at),
            'task_count': len(u.tasks),
        })
    return result, 200


def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]
    return data, 200


def create_user(payload):
    data = validate_create_user(payload)
    if User.query.filter_by(email=data['email']).first():
        raise ConflictError('Email já cadastrado')

    user = User(name=data['name'], email=data['email'], role=data['role'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    logger.info("Usuário criado: %s - %s", user.id, user.name)
    return user.to_dict(), 201


def update_user(user_id, payload):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    if not payload:
        raise AppError('Dados inválidos')

    if 'name' in payload:
        user.name = payload['name']
    if 'email' in payload:
        if not _EMAIL_RE.match(payload['email']):
            raise AppError('Email inválido')
        existing = User.query.filter_by(email=payload['email']).first()
        if existing and existing.id != user_id:
            raise ConflictError('Email já cadastrado')
        user.email = payload['email']
    if 'password' in payload:
        if len(payload['password']) < MIN_PASSWORD_LENGTH:
            raise AppError('Senha muito curta')
        user.set_password(payload['password'])
    if 'role' in payload:
        if payload['role'] not in VALID_ROLES:
            raise AppError('Role inválido')
        user.role = payload['role']
    if 'active' in payload:
        user.active = payload['active']

    db.session.commit()
    return user.to_dict(), 200


def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    for t in Task.query.filter_by(user_id=user_id).all():
        db.session.delete(t)
    db.session.delete(user)
    db.session.commit()
    logger.info("Usuário deletado: %s", user_id)
    return {'message': 'Usuário deletado com sucesso'}, 200


def get_user_tasks(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    result = []
    for t in Task.query.filter_by(user_id=user_id).all():
        item = {
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'status': t.status,
            'priority': t.priority,
            'created_at': str(t.created_at),
            'due_date': str(t.due_date) if t.due_date else None,
            'overdue': t.is_overdue(),
        }
        result.append(item)
    return result, 200


def login(payload):
    data = validate_login(payload)
    user = User.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        raise UnauthorizedError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')
    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': issue_access_token(user.id),
    }, 200
