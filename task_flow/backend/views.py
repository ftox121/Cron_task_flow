from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.models import Task, ExecutionLog
from backend.serializers import TaskSerializer, ExecutionLogSerializer
from backend.tasks import check_and_run_tasks, send_daily_newsletter, backup_database, check_inactive_users, clear_cache


from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from backend.models import Task
from .serializers import TaskSerializer, PeriodicTaskSerializer


class TaskViewSet(viewsets.ViewSet):  # Используем ViewSet вместо ModelViewSet
    def list(self, request):
        tasks = Task.objects.all()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def retrieve(self, request, pk=None):
        task = Task.objects.get(pk=pk)
        serializer = TaskSerializer(task)
        return Response(serializer.data)

    def update(self, request, pk=None):
        task = Task.objects.get(pk=pk)
        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def destroy(self, request, pk=None):
        task = Task.objects.get(pk=pk)
        task.delete()
        return Response(status=204)


class DetailView(generics.RetrieveUpdateDestroyAPIView):
    """Просмотр , обновление, удаление задач """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class ExecutionLogListView(generics.ListAPIView):
    """Просмотр логов выполнения задач"""
    queryset = ExecutionLog.objects.all().order_by("-executed_at")
    serializer_class = ExecutionLogSerializer


class CheckAndRunTasksView(APIView):
    def post(self, request, *args, **kwargs):
        check_and_run_tasks.delay()  # Отправляем задачу в очередь Celery
        return Response({"message": "Задача 'check_and_run_tasks' поставлена в очередь."}, status=status.HTTP_202_ACCEPTED)


class SendDailyNewsletterView(APIView):
    def post(self, request, *args, **kwargs):
        send_daily_newsletter.delay()
        return Response({"message": "Задача 'send_daily_newsletter' поставлена в очередь."}, status=status.HTTP_202_ACCEPTED)


class BackupDatabaseView(APIView):
    def post(self, request, *args, **kwargs):
        backup_database.delay()  # Отправляем задачу в очередь Celery
        return Response({"message": "Задача 'backup_database' поставлена в очередь."}, status=status.HTTP_202_ACCEPTED)


class CheckInactiveUsersView(APIView):
    def post(self, request, *args, **kwargs):
        check_inactive_users.delay()  # Отправляем задачу в очередь Celery
        return Response({"message": "Задача 'check_inactive_users' поставлена в очередь."}, status=status.HTTP_202_ACCEPTED)


class ClearCacheView(APIView):
    def post(self, request, *args, **kwargs):
        clear_cache.delay()  # Отправляем задачу в очередь Celery
        return Response({"message": "Задача 'clear_cache' поставлена в очередь."}, status=status.HTTP_202_ACCEPTED)
