from django.contrib import admin

from backend.models import Task, ExecutionLog


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'cron_expression', 'status', 'user')
    search_fields = ('name', 'cron_expression')


@admin.register(ExecutionLog)
class ExecutionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'status', 'executed_at')
    search_fields = ('task__name',)