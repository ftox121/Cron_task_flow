from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    cron_expression = models.CharField(max_length=50, verbose_name='Cron-выражение')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name='Статус')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    def __str__(self):
        return f'{self.name} ({self.cron_expression})'


class ExecutionLog(models.Model):

    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed')
    ]
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='logs', verbose_name='Задача')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='Статус выполнения')
    result = models.CharField(max_length=32, verbose_name='Результат выполнения')
    executed_at = models.DateTimeField(auto_now_add=True, verbose_name='Время выполнения')

    def __str__(self):
        return f'Execution a {self.task.name} at {self.executed_at}'