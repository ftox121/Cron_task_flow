from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from .models import Task
import json


@receiver(post_save, sender=Task)
def sync_periodic_task(sender, instance, created, **kwargs):
    cron_parts = instance.cron_expression.split()
    if len(cron_parts) != 5:
        print("Неверное cron выражение")
        return

    # Создаём или обновляем расписание
    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute=cron_parts[0],
        hour=cron_parts[1],
        day_of_month=cron_parts[2],
        month_of_year=cron_parts[3],
        day_of_week=cron_parts[4],
    )

    # Если задача уже была создана (не created), обновляем её
    if not created and instance.periodic_task:
        periodic_task = instance.periodic_task
        periodic_task.crontab = schedule
        periodic_task.enabled = instance.is_active
        periodic_task.save()
    else:
        # Создаём новую PeriodicTask и привязываем к Task
        periodic_task = PeriodicTask.objects.create(
            crontab=schedule,
            name=f'task-{instance.id}-{instance.name}',
            task='backend.tasks.execute_custom_task',
            args=json.dumps([instance.id]),
            enabled=instance.is_active,
        )
        instance.periodic_task = periodic_task
        instance.save()  # Важно: сохраняем связь


@receiver(pre_delete, sender=Task)
def delete_periodic_task(sender, instance, **kwargs):
    if instance.periodic_task:
        instance.periodic_task.delete()