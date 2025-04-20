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


class PeriodicTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodicTask
        fields = ['id', 'name', 'task', 'enabled', 'last_run_at', 'date_changed']
