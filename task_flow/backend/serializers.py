from rest_framework import serializers
from backend.models import Task, ExecutionLog


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["id", "name", "description", "cron_expression", "status"]


class ExecutionLogSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)

    class Meta:
        model = ExecutionLog
        fields = ["id", "task", "status", "result", "executed_at"]