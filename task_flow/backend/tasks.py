from celery import shared_task
from croniter import croniter
from django.core.mail import send_mail

from .models import Task, ExecutionLog, TaskStatus
from datetime import datetime
import pytz


@shared_task
def check_and_run_tasks():
    now = datetime.now(pytz.utc)

    for task in Task.objects.filter(is_active=True):
        cron = croniter(task.cron_expression, task.logs.last().executed_at if task.logs.exists() else now)
        next_time = cron.get_next(datetime)

        # Проверка: если next_time <= now, значит пора выполнять
        if next_time <= now:
            # Обновим статус
            task.status = 'running'
            task.save()

            # Тут вместо реального запуска просто фиктивный результат
            result = f'Выполнено в {now.strftime("%H:%M:%S")}'

            # Логируем результат
            ExecutionLog.objects.create(
                task=task,
                status='success',
                result=result
            )

            task.status = 'completed'
            task.save()


@shared_task
def send_daily_newsletter():
    TaskStatus.objects.create(task_name="send_daily_newsletter", status="running")

    from django.contrib.auth.models import User
    subject = "Ежедневное обновление"
    message = "Привет! Вот ваше обновление на сегодня."
    for user in User.objects.all():
        send_mail(subject, message, 'admin@example.com', [user.email])

    TaskStatus.objects.filter(task_name="send_daily_newsletter").update(status="completed",
                                                                        result="Уведомления отправлены")


@shared_task
def backup_database():
    import subprocess
    command = "pg_dump -U postgres -h localhost -F c tasks_db > /backups/tasks_db_backup.sql"
    subprocess.run(command, shell=True)
    print("Резервная копия базы данных создана.")


@shared_task
def check_inactive_users():
    from datetime import timedelta
    from django.utils import timezone
    from django.contrib.auth.models import User
    inactive_threshold = timezone.now() - timedelta(days=30)
    inactive_users = User.objects.filter(last_login__lt=inactive_threshold)
    for user in inactive_users:
        # Например, отправка email:
        send_mail("Вы не активны на нашем сайте", "Пожалуйста, войдите, чтобы активировать свою учетную запись.", 'admin@example.com', [user.email])
    print("Проверены неактивные пользователи.")


@shared_task
def clear_cache():
    from django.core.cache import cache
    cache.clear()
    print("Кэш очищен.")


import datetime

@shared_task
def execute_custom_task(task_id):
    print(f"[{datetime.datetime.now()}] Задача {task_id} выполнена.")
    return f"Task {task_id} executed at {datetime.datetime.now()}"