"""Script para popular o banco com dados iniciais"""
from app import app, db
from models.task import Task
from models.user import User
from models.category import Category
from datetime import timedelta
from utils.timeutils import utc_now


def seed_data():
    with app.app_context():
        Task.query.delete()
        User.query.delete()
        Category.query.delete()
        db.session.commit()

        u1 = User()
        u1.name = 'João Silva'
        u1.email = 'joao@email.com'
        # Senhas de seed: apenas demonstração acadêmica local (não são credenciais reais).
        u1.set_password('1234')
        u1.role = 'admin'
        db.session.add(u1)

        u2 = User()
        u2.name = 'Maria Santos'
        u2.email = 'maria@email.com'
        u2.set_password('abcd')
        u2.role = 'user'
        db.session.add(u2)

        u3 = User()
        u3.name = 'Pedro Oliveira'
        u3.email = 'pedro@email.com'
        u3.set_password('pass')
        u3.role = 'manager'
        db.session.add(u3)

        db.session.commit()

        c1 = Category(name='Backend', description='Tarefas de backend', color='#3498db')
        c2 = Category(name='Frontend', description='Tarefas de frontend', color='#2ecc71')
        c3 = Category(name='DevOps', description='Tarefas de infraestrutura', color='#e74c3c')
        c4 = Category(name='Bug', description='Correção de bugs', color='#e67e22')
        db.session.add_all([c1, c2, c3, c4])
        db.session.commit()

        now = utc_now()
        tasks_data = [
            {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT', 'status': 'pending', 'priority': 1, 'user_id': u1.id, 'category_id': c1.id, 'due_date': now - timedelta(days=3)},
            {'title': 'Criar tela de login', 'description': 'Tela de login responsiva', 'status': 'in_progress', 'priority': 2, 'user_id': u2.id, 'category_id': c2.id, 'due_date': now + timedelta(days=5)},
            {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions', 'status': 'done', 'priority': 2, 'user_id': u3.id, 'category_id': c3.id, 'tags': 'devops,ci,github'},
            {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais', 'status': 'pending', 'priority': 1, 'user_id': u1.id, 'category_id': c4.id, 'due_date': now - timedelta(days=1)},
            {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros', 'status': 'pending', 'priority': 3, 'user_id': u1.id, 'category_id': c1.id, 'due_date': now + timedelta(days=10)},
            {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%', 'status': 'pending', 'priority': 2, 'user_id': u2.id, 'category_id': c1.id},
            {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática', 'status': 'cancelled', 'priority': 4, 'user_id': u3.id, 'category_id': c1.id},
            {'title': 'Refatorar models', 'description': 'Melhorar organização dos models', 'status': 'in_progress', 'priority': 3, 'user_id': u2.id, 'category_id': c1.id, 'tags': 'refactor,tech-debt'},
            {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana', 'status': 'pending', 'priority': 4, 'user_id': u3.id, 'category_id': c3.id, 'due_date': now + timedelta(days=20)},
            {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic', 'status': 'pending', 'priority': 3, 'user_id': u1.id, 'category_id': c1.id, 'tags': 'improvement,validation'},
        ]

        for td in tasks_data:
            t = Task()
            t.title = td['title']
            t.description = td['description']
            t.status = td['status']
            t.priority = td['priority']
            t.user_id = td['user_id']
            t.category_id = td['category_id']
            if 'due_date' in td:
                t.due_date = td['due_date']
            if 'tags' in td:
                t.tags = td['tags']
            db.session.add(t)

        db.session.commit()
        print("Seed concluído com sucesso!")
        print(f"  {User.query.count()} usuários")
        print(f"  {Category.query.count()} categorias")
        print(f"  {Task.query.count()} tasks")


if __name__ == '__main__':
    seed_data()
