import logging
import smtplib
from config import settings
from utils.timeutils import utc_now

logger = logging.getLogger(__name__)


class NotificationService:
    """Service de notificação — usa config/env; SMTP só se SMTP_ENABLED=true."""

    def __init__(self):
        self.notifications = []
        self.email_host = settings.SMTP_HOST
        self.email_port = settings.SMTP_PORT
        self.email_user = settings.SMTP_USER
        self.email_password = settings.SMTP_PASSWORD
        self.enabled = settings.SMTP_ENABLED

    def send_email(self, to, subject, body):
        if not self.enabled or not self.email_user:
            logger.info("SMTP desabilitado — notificação não enviada para %s", to)
            return False
        try:
            server = smtplib.SMTP(self.email_host, self.email_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(self.email_user, to, message)
            server.quit()
            logger.info("Email enviado para %s", to)
            return True
        except Exception as e:
            logger.warning("Erro ao enviar email: %s", e)
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        self.send_email(user.email, subject, body)
        self.notifications.append({
            'type': 'task_assigned',
            'user_id': user.id,
            'task_id': task.id,
            'timestamp': utc_now(),
        })

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\n"
            f"Data limite: {task.due_date}"
        )
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [n for n in self.notifications if n['user_id'] == user_id]


notification_service = NotificationService()
