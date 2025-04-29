from celery import shared_task
from croniter import croniter
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Task, ExecutionLog, TaskStatus
from datetime import datetime, timedelta
import pytz
import requests
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


# Основная задача для проверки и запуска задач по расписанию
@shared_task(bind=True)
def check_and_run_scheduled_tasks(self):
    """
    Проверяет и запускает запланированные задачи по их cron-расписанию.
    """
    now = timezone.now()

    try:
        with transaction.atomic():
            # Блокируем задачи для предотвращения конкурентного выполнения
            tasks = Task.objects.select_for_update().filter(
                is_active=True,
                status__in=['pending', 'failed']  # Только задачи, готовые к выполнению
            )

            for task in tasks:
                try:
                    # Проверяем по cron, нужно ли выполнять задачу сейчас
                    last_execution = task.logs.last().executed_at if task.logs.exists() else now
                    cron = croniter(task.cron_expression, last_execution)
                    next_run = cron.get_next(datetime)

                    if next_run > now:
                        continue  # Еще не время выполнять

                    # Обновляем статус и время последнего выполнения
                    task.status = 'running'
                    task.save()

                    # Логируем начало выполнения
                    ExecutionLog.objects.create(
                        task=task,
                        status='success',
                        result=f"Task {task.id} started execution"
                    )

                    # Запускаем задачу в зависимости от типа (можно добавить больше типов)
                    if 'email' in task.name.lower():
                        async_result = send_user_notifications.delay(task.id)
                    else:
                        async_result = execute_generic_task.delay(task.id)

                    # Обновляем запись задачи
                    task.save()

                except Exception as e:
                    logger.error(f"Error processing task {task.id}: {str(e)}")
                    ExecutionLog.objects.create(
                        task=task,
                        status='failed',
                        result=f"Error: {str(e)}"
                    )
                    task.status = 'failed'
                    task.save()

    except Exception as e:
        logger.error(f"Error in check_and_run_scheduled_tasks: {str(e)}")
        raise self.retry(exc=e, countdown=60)


@shared_task
def send_user_notifications(task_id):
    """
    Отправка уведомлений пользователям (email)
    """
    try:
        task = Task.objects.get(id=task_id)
        users = User.objects.filter(is_active=True)

        subject = f"Уведомление: {task.name}"
        message = task.description or "Это автоматическое уведомление от системы."

        sent_count = 0
        for user in users:
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Error sending email to {user.email}: {str(e)}")

        result = f"Successfully sent {sent_count} notifications"
        ExecutionLog.objects.create(
            task=task,
            status='success',
            result=result
        )
        task.status = 'completed'
        task.save()
        return result

    except Exception as e:
        logger.error(f"Error in send_user_notifications: {str(e)}")
        ExecutionLog.objects.create(
            task=task,
            status='failed',
            result=f"Error: {str(e)}"
        )
        task.status = 'failed'
        task.save()
        raise


@shared_task
def execute_generic_task(task_id):
    """
    Универсальная задача для выполнения произвольного кода
    """
    task = Task.objects.get(id=task_id)
    try:
        # Здесь может быть любой код, специфичный для задачи
        # Например, можно добавить логику в описание задачи
        result = f"Task {task_id} executed successfully"

        ExecutionLog.objects.create(
            task=task,
            status='success',
            result=result
        )
        task.status = 'completed'
        task.save()
        return result
    except Exception as e:
        logger.error(f"Error in execute_generic_task: {str(e)}")
        ExecutionLog.objects.create(
            task=task,
            status='failed',
            result=f"Error: {str(e)}"
        )
        task.status = 'failed'
        task.save()
        raise


@shared_task
def cleanup_old_data():
    """
    Очистка устаревших данных (логов, временных файлов и т.д.)
    """
    try:
        # Очистка старых логов (старше 30 дней)
        retention_period = timezone.now() - timedelta(days=30)
        deleted_logs, _ = ExecutionLog.objects.filter(
            executed_at__lt=retention_period
        ).delete()

        # Очистка статусов задач (старше 7 дней)
        completed_tasks, _ = TaskStatus.objects.filter(
            timestamp__lt=timezone.now() - timedelta(days=7)
        ).delete()

        result = f"Cleaned up: {deleted_logs} old logs and {completed_tasks} task statuses"
        TaskStatus.objects.create(
            task_name="cleanup_old_data",
            status="completed",
            result=result
        )
        return result
    except Exception as e:
        logger.error(f"Error in cleanup_old_data: {str(e)}")
        TaskStatus.objects.create(
            task_name="cleanup_old_data",
            status="failed",
            result=f"Error: {str(e)}"
        )
        raise


@shared_task
def backup_database():
    """
    Создание резервной копии базы данных в Docker-окружении
    """
    try:
        import subprocess
        from datetime import datetime
        import os
        from django.conf import settings

        # Параметры подключения к БД
        db = settings.DATABASES['default']

        # Настройки бэкапа
        backup_dir = "/backups"
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/db_backup_{timestamp}.dump"

        # Команда для создания бэкапа
        command = [
            'pg_dump',
            '-h', db['HOST'],
            '-p', str(db['PORT']),
            '-U', db['USER'],
            '-d', db['NAME'],
            '-F', 'c',  # custom format (сжатый)
            '-f', backup_file
        ]

        # Переменные окружения для аутентификации
        env = os.environ.copy()
        env['PGPASSWORD'] = db['PASSWORD']

        # Запуск команды
        result = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            status_msg = f"Backup created: {backup_file}"
            # Проверяем размер файла
            if os.path.getsize(backup_file) == 0:
                status_msg = "Backup failed: Empty backup file"
                raise Exception(status_msg)
        else:
            status_msg = f"Backup failed: {result.stderr}"
            raise Exception(status_msg)

        TaskStatus.objects.create(
            task_name="backup_database",
            status="completed",
            result=status_msg
        )
        return status_msg

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        TaskStatus.objects.create(
            task_name="backup_database",
            status="failed",
            result=error_msg
        )
        logger.error(f"Backup failed: {error_msg}")
        raise


@shared_task
def check_inactive_users():
    """
    Проверка неактивных пользователей и отправка уведомлений
    """
    try:
        inactive_threshold = timezone.now() - timedelta(days=30)
        inactive_users = User.objects.filter(
            last_login__lt=inactive_threshold,
            is_active=True
        )

        notified_count = 0
        for user in inactive_users:
            try:
                send_mail(
                    "Мы скучаем по вам!",
                    "Вы не заходили в систему более 30 дней. Вернитесь!",
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True
                )
                notified_count += 1
            except Exception as e:
                logger.error(f"Error notifying inactive user {user.email}: {str(e)}")

        result = f"Notified {notified_count} inactive users"
        TaskStatus.objects.create(
            task_name="check_inactive_users",
            status="completed",
            result=result
        )
        return result
    except Exception as e:
        logger.error(f"Error in check_inactive_users: {str(e)}")
        TaskStatus.objects.create(
            task_name="check_inactive_users",
            status="failed",
            result=f"Error: {str(e)}"
        )
        raise