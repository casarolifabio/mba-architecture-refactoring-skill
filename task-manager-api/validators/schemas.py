from datetime import datetime
import re
from middlewares.error_handler import AppError
from utils.helpers import VALID_STATUSES, VALID_ROLES, MIN_TITLE_LENGTH, MAX_TITLE_LENGTH, MIN_PASSWORD_LENGTH


def parse_tags(tags):
    if tags is None:
        return None
    if isinstance(tags, list):
        return ','.join(tags)
    return tags


def parse_due_date(value, required_format_message='Formato de data inválido. Use YYYY-MM-DD'):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d')
    except (TypeError, ValueError):
        raise AppError(required_format_message)


def validate_create_task(data):
    if not data:
        raise AppError('Dados inválidos')
    title = data.get('title')
    if not title:
        raise AppError('Título é obrigatório')
    if len(title) < MIN_TITLE_LENGTH:
        raise AppError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise AppError('Título muito longo')

    status = data.get('status', 'pending')
    priority = data.get('priority', 3)
    if status not in VALID_STATUSES:
        raise AppError('Status inválido')
    if priority < 1 or priority > 5:
        raise AppError('Prioridade deve ser entre 1 e 5')

    return {
        'title': title,
        'description': data.get('description', ''),
        'status': status,
        'priority': priority,
        'user_id': data.get('user_id'),
        'category_id': data.get('category_id'),
        'due_date': parse_due_date(data.get('due_date')),
        'tags': parse_tags(data.get('tags')),
    }


def validate_update_task(data):
    if not data:
        raise AppError('Dados inválidos')
    payload = {}
    if 'title' in data:
        if len(data['title']) < MIN_TITLE_LENGTH:
            raise AppError('Título muito curto')
        if len(data['title']) > MAX_TITLE_LENGTH:
            raise AppError('Título muito longo')
        payload['title'] = data['title']
    if 'description' in data:
        payload['description'] = data['description']
    if 'status' in data:
        if data['status'] not in VALID_STATUSES:
            raise AppError('Status inválido')
        payload['status'] = data['status']
    if 'priority' in data:
        if data['priority'] < 1 or data['priority'] > 5:
            raise AppError('Prioridade deve ser entre 1 e 5')
        payload['priority'] = data['priority']
    if 'user_id' in data:
        payload['user_id'] = data['user_id']
    if 'category_id' in data:
        payload['category_id'] = data['category_id']
    if 'due_date' in data:
        if data['due_date']:
            payload['due_date'] = parse_due_date(
                data['due_date'], 'Formato de data inválido'
            )
        else:
            payload['due_date'] = None
    if 'tags' in data:
        payload['tags'] = parse_tags(data['tags'])
    return payload


_EMAIL_RE = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')


def validate_create_user(data):
    if not data:
        raise AppError('Dados inválidos')
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')
    if not name:
        raise AppError('Nome é obrigatório')
    if not email:
        raise AppError('Email é obrigatório')
    if not password:
        raise AppError('Senha é obrigatória')
    if not _EMAIL_RE.match(email):
        raise AppError('Email inválido')
    if len(password) < MIN_PASSWORD_LENGTH:
        raise AppError('Senha deve ter no mínimo 4 caracteres')
    if role not in VALID_ROLES:
        raise AppError('Role inválido')
    return {'name': name, 'email': email, 'password': password, 'role': role}


def validate_login(data):
    if not data:
        raise AppError('Dados inválidos')
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise AppError('Email e senha são obrigatórios')
    return {'email': email, 'password': password}
