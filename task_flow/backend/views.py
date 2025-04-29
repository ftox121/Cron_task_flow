from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django_celery_beat.models import PeriodicTask

from .models import Task, ExecutionLog, TaskStatus
from .serializers import (
    TaskSerializer,
    ExecutionLogSerializer,
    PeriodicTaskSerializer
)
from .tasks import (
    check_and_run_scheduled_tasks,
    send_user_notifications,
    execute_generic_task,
    cleanup_old_data,
    backup_database,
    check_inactive_users
)

from rest_framework import mixins


class PeriodicTaskViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    API для управления периодическими задачами Celery Beat

    Поддерживает:
    - Создание новых периодических задач (POST)
    - Просмотр списка задач (GET)
    - Активацию/деактивацию задач (POST toggle)
    """
    queryset = PeriodicTask.objects.all()
    serializer_class = PeriodicTaskSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """Активация/деактивация периодической задачи"""
        task = self.get_object()
        task.enabled = not task.enabled
        task.save()
        return Response({
            'status': 'success',
            'enabled': task.enabled
        })

class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления задачами с поддержкой Celery Beat
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Ручной запуск задачи"""
        task = self.get_object()
        if 'email' in task.name.lower():
            async_result = send_user_notifications.delay(task.id)
        else:
            async_result = execute_generic_task.delay(task.id)
        return Response({
            'status': 'Task started',
            'celery_task_id': async_result.id
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Активация/деактивация задачи"""
        task = self.get_object()
        task.is_active = not task.is_active
        task.save()
        if task.periodic_task:
            task.periodic_task.enabled = task.is_active
            task.periodic_task.save()
        return Response({
            'status': 'success',
            'is_active': task.is_active
        })

    @action(detail=False, methods=['get'])
    def mine(self, request):
        """Получение задач текущего пользователя"""
        tasks = Task.objects.filter(user=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def periodic_info(self, request, pk=None):
        """Получение информации о периодической задаче"""
        task = self.get_object()
        if not task.periodic_task:
            return Response(
                {'detail': 'No periodic task associated'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = PeriodicTaskSerializer(task.periodic_task)
        return Response(serializer.data)

class ExecutionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Просмотр логов выполнения задач
    """
    serializer_class = ExecutionLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ExecutionLog.objects.filter(
            task__user=self.request.user
        ).order_by('-executed_at')

    @action(detail=False, methods=['get'])
    def task_logs(self, request, task_id=None):
        """Логи конкретной задачи"""
        task = get_object_or_404(Task, id=task_id, user=request.user)
        logs = ExecutionLog.objects.filter(task=task).order_by('-executed_at')
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)

class SystemTasksAPIView(generics.GenericAPIView):
    """
    API для управления системными задачами
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, task_name):
        """Запуск системной задачи"""
        task_mapping = {
            'check_and_run': check_and_run_scheduled_tasks,
            'cleanup': cleanup_old_data,
            'backup': backup_database,
            'check_inactive': check_inactive_users
        }

        if task_name not in task_mapping:
            return Response(
                {'error': 'Unknown task name'},
                status=status.HTTP_400_BAD_REQUEST
            )

        async_result = task_mapping[task_name].delay()
        return Response({
            'status': f'Task {task_name} started',
            'celery_task_id': async_result.id
        }, status=status.HTTP_202_ACCEPTED)

    def get(self, request):
        """Получение статуса системных задач"""
        statuses = TaskStatus.objects.all().order_by('-timestamp')[:50]
        data = [{
            'id': status.id,
            'task_name': status.task_name,
            'status': status.status,
            'timestamp': status.timestamp,
            'result': status.result
        } for status in statuses]
        return Response(data)

class TaskStatsAPIView(generics.GenericAPIView):
    """
    Статистика по задачам
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Count, Q

        user_stats = Task.objects.filter(
            user=request.user
        ).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
            pending=Count('id', filter=Q(status='pending')),
            running=Count('id', filter=Q(status='running')),
            completed=Count('id', filter=Q(status='completed')),
            failed=Count('id', filter=Q(status='failed'))
        )

        recent_executions = ExecutionLog.objects.filter(
            task__user=request.user
        ).order_by('-executed_at')[:5]
        execution_serializer = ExecutionLogSerializer(recent_executions, many=True)

        return Response({
            'user_stats': user_stats,
            'recent_executions': execution_serializer.data
        })