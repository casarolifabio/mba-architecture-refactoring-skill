from database import db
from models.task import Task
from models.user import User
from models.category import Category
from datetime import timedelta
from middlewares.error_handler import AppError, NotFoundError
from utils.timeutils import utc_now


def summary_report():
    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    p1 = Task.query.filter_by(priority=1).count()
    p2 = Task.query.filter_by(priority=2).count()
    p3 = Task.query.filter_by(priority=3).count()
    p4 = Task.query.filter_by(priority=4).count()
    p5 = Task.query.filter_by(priority=5).count()

    now = utc_now()
    overdue_list = []
    for t in Task.query.all():
        if t.is_overdue():
            overdue_list.append({
                'id': t.id,
                'title': t.title,
                'due_date': str(t.due_date),
                'days_overdue': (now - t.due_date).days,
            })

    seven_days_ago = now - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(
        Task.status == 'done',
        Task.updated_at >= seven_days_ago,
    ).count()

    user_stats = []
    for u in User.query.all():
        user_tasks = Task.query.filter_by(user_id=u.id).all()
        total = len(user_tasks)
        completed = sum(1 for t in user_tasks if t.status == 'done')
        user_stats.append({
            'user_id': u.id,
            'user_name': u.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': round((completed / total) * 100, 2) if total > 0 else 0,
        })

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': total_users,
            'total_categories': total_categories,
        },
        'tasks_by_status': {
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'cancelled': cancelled,
        },
        'tasks_by_priority': {
            'critical': p1,
            'high': p2,
            'medium': p3,
            'low': p4,
            'minimal': p5,
        },
        'overdue': {
            'count': len(overdue_list),
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': recent_tasks,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_stats,
    }, 200


def user_report(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')

    tasks = Task.query.filter_by(user_id=user_id).all()
    total = len(tasks)
    done = sum(1 for t in tasks if t.status == 'done')
    pending = sum(1 for t in tasks if t.status == 'pending')
    in_progress = sum(1 for t in tasks if t.status == 'in_progress')
    cancelled = sum(1 for t in tasks if t.status == 'cancelled')
    overdue = sum(1 for t in tasks if t.is_overdue())
    high_priority = sum(1 for t in tasks if t.priority <= 2)

    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            'done': done,
            'pending': pending,
            'in_progress': in_progress,
            'cancelled': cancelled,
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
        },
    }, 200


def list_categories():
    result = []
    for c in Category.query.all():
        cat_data = c.to_dict()
        cat_data['task_count'] = Task.query.filter_by(category_id=c.id).count()
        result.append(cat_data)
    return result, 200


def create_category(payload):
    if not payload:
        raise AppError('Dados inválidos')
    name = payload.get('name')
    if not name:
        raise AppError('Nome é obrigatório')
    category = Category(
        name=name,
        description=payload.get('description', ''),
        color=payload.get('color', '#000000'),
    )
    db.session.add(category)
    db.session.commit()
    return category.to_dict(), 201


def update_category(cat_id, payload):
    cat = db.session.get(Category, cat_id)
    if not cat:
        raise NotFoundError('Categoria não encontrada')
    if not payload:
        raise AppError('Dados inválidos')
    if 'name' in payload:
        cat.name = payload['name']
    if 'description' in payload:
        cat.description = payload['description']
    if 'color' in payload:
        cat.color = payload['color']
    db.session.commit()
    return cat.to_dict(), 200


def delete_category(cat_id):
    cat = db.session.get(Category, cat_id)
    if not cat:
        raise NotFoundError('Categoria não encontrada')
    db.session.delete(cat)
    db.session.commit()
    return {'message': 'Categoria deletada'}, 200
