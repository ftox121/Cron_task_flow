from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_flow.settings')

app = Celery('task_flow')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check-tasks-every-minute': {
        'task': 'backend.tasks.check_and_run_tasks',
        'schedule': crontab(minute='*'),
    },
}