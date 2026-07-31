import logging
from database import db
from models.task import Task
from models.user import User
from models.category import Category
from sqlalchemy.orm import joinedload
from middlewares.error_handler import AppError, NotFoundError
from validators.schemas import validate_create_task, validate_update_task
from services.notification_service import notification_service
from utils.timeutils import utc_now

logger = logging.getLogger(__name__)


def _serialize_task_list_item(task):
    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data


def list_tasks():
    tasks = Task.query.options(
        joinedload(Task.user),
        joinedload(Task.category),
    ).all()
    return [_serialize_task_list_item(t) for t in tasks], 200


def get_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    return data, 200


def create_task(payload):
    data = validate_create_task(payload)

    user = None
    if data['user_id']:
        user = db.session.get(User, data['user_id'])
        if not user:
            raise NotFoundError('Usuário não encontrado')

    if data['category_id']:
        cat = db.session.get(Category, data['category_id'])
        if not cat:
            raise NotFoundError('Categoria não encontrada')

    task = Task(
        title=data['title'],
        description=data['description'],
        status=data['status'],
        priority=data['priority'],
        user_id=data['user_id'],
        category_id=data['category_id'],
        due_date=data['due_date'],
        tags=data['tags'],
    )
    db.session.add(task)
    db.session.commit()
    logger.info("Task criada: %s - %s", task.id, task.title)

    if user:
        notification_service.notify_task_assigned(user, task)

    return task.to_dict(), 201


def update_task(task_id, payload):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError('Task não encontrada')

    data = validate_update_task(payload)

    if 'user_id' in data and data['user_id']:
        if not db.session.get(User, data['user_id']):
            raise NotFoundError('Usuário não encontrado')
    if 'category_id' in data and data['category_id']:
        if not db.session.get(Category, data['category_id']):
            raise NotFoundError('Categoria não encontrada')

    for key, value in data.items():
        setattr(task, key, value)
    task.updated_at = utc_now()
    db.session.commit()
    logger.info("Task atualizada: %s", task.id)
    return task.to_dict(), 200


def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    db.session.delete(task)
    db.session.commit()
    logger.info("Task deletada: %s", task_id)
    return {'message': 'Task deletada com sucesso'}, 200


def search_tasks(q='', status='', priority='', user_id=''):
    query = Task.query
    if q:
        query = query.filter(
            db.or_(
                Task.title.like(f'%{q}%'),
                Task.description.like(f'%{q}%'),
            )
        )
    if status:
        query = query.filter(Task.status == status)
    if priority:
        try:
            query = query.filter(Task.priority == int(priority))
        except ValueError:
            raise AppError('Prioridade inválida')
    if user_id:
        try:
            query = query.filter(Task.user_id == int(user_id))
        except ValueError:
            raise AppError('user_id inválido')
    return [t.to_dict() for t in query.all()], 200


def task_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()
    overdue_count = sum(1 for t in Task.query.all() if t.is_overdue())
    return {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'done': done,
        'cancelled': cancelled,
        'overdue': overdue_count,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
    }, 200
