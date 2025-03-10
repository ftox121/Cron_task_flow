from django.shortcuts import render
from rest_framework import generics, permissions

from backend.models import Task, ExecutionLog
from backend.serializers import TaskSerializer, ExecutionLogSerializer


class CreateTaskView(generics.ListCreateAPIView):
    """Список и создание задач """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DetailView(generics.RetrieveUpdateDestroyAPIView):
    """Просмотр , обновление, удаление задач """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class ExecutionLogListView(generics.ListAPIView):
    """Просмотр логов выполнения задач"""
    queryset = ExecutionLog.objects.all().order_by("-executed_at")
    serializer_class = ExecutionLogSerializer
