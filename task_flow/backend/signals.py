from django.db.models.signals import post_save
from django.dispatch import receiver
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from .models import Task
import json


@receiver(post_save, sender=Task)
def create_periodic_task(sender, instance, created, **kwargs):
    if not created:
        return

    # Разбираем cron выражение
    cron_parts = instance.cron_expression.split()
    if len(cron_parts) != 5:
        print("Неверное cron выражение")
        return

    # Создаем или получаем расписание
    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute=cron_parts[0],
        hour=cron_parts[1],
        day_of_month=cron_parts[2],
        month_of_year=cron_parts[3],
        day_of_week=cron_parts[4],
    )

    # Создаем PeriodicTask
    PeriodicTask.objects.create(
        crontab=schedule,
        name=f'task-{instance.id}',
        task='backend.tasks.execute_custom_task',  # Имя твоей Celery задачи
        args=json.dumps([instance.id]),
        enabled=instance.is_active
    )