from rest_framework import serializers
from backend.models import Task, ExecutionLog


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["id", "name", "description", "cron_expression", "status", "user", "is_active"]

    def create(self, validated_data):
        task_name = validated_data['name']
        cron_expression = validated_data['cron_expression']

        # Создаем новый IntervalSchedule
        schedule, created = IntervalSchedule.objects.get_or_create(every=5, period=IntervalSchedule.MINUTES)

        # Создаем задачу в PeriodicTask
        periodic_task = PeriodicTask.objects.create(
            name=task_name,
            task="backend.tasks.check_and_run_tasks",
            interval=schedule,
            enabled=True,
            crontab=None,  # Используем cron для расписания
            one_off=False
        )

        # Создаем задачу в модели Task
        task = Task.objects.create(
            name=task_name,
            description=validated_data.get('description', ''),
            cron_expression=cron_expression,
            status='pending',
            user=validated_data['user'],
            periodic_task=periodic_task
        )
        return task


class ExecutionLogSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)

    class Meta:
        model = ExecutionLog
        fields = ["id", "task", "status", "result", "executed_at"]


from rest_framework import serializers
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from rest_framework import serializers
from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule
import json


class PeriodicTaskSerializer(serializers.ModelSerializer):
    # Поля для создания расписания (write-only)
    crontab = serializers.DictField(child=serializers.CharField(), write_only=True, required=False)
    interval = serializers.DictField(child=serializers.CharField(), write_only=True, required=False)

    class Meta:
        model = PeriodicTask
        fields = [
            'id', 'name', 'task', 'enabled', 'last_run_at', 'date_changed',
            'crontab', 'interval', 'args', 'kwargs'
        ]
        read_only_fields = ['last_run_at', 'date_changed']

    def create(self, validated_data):
        crontab_data = validated_data.pop('crontab', None)
        interval_data = validated_data.pop('interval', None)

        # Создаем расписание
        if crontab_data:
            schedule, _ = CrontabSchedule.objects.get_or_create(
                minute=crontab_data.get('minute', '*'),
                hour=crontab_data.get('hour', '*'),
                day_of_week=crontab_data.get('day_of_week', '*'),
                day_of_month=crontab_data.get('day_of_month', '*'),
                month_of_year=crontab_data.get('month_of_year', '*'),
            )
            validated_data['crontab'] = schedule
        elif interval_data:
            schedule, _ = IntervalSchedule.objects.get_or_create(
                every=interval_data['every'],
                period=interval_data['period'],
            )
            validated_data['interval'] = schedule

        # Сериализуем args и kwargs
        if 'args' in validated_data:
            validated_data['args'] = json.dumps(validated_data['args'])
        if 'kwargs' in validated_data:
            validated_data['kwargs'] = json.dumps(validated_data['kwargs'])

        return super().create(validated_data)