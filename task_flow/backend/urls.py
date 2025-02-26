from django.urls import path

from backend.views import CreateTaskView, DetailView, ExecutionLogListView

urlpatterns = [
    path('tasks/', CreateTaskView.as_view(),name='task_create'),
    path('tasks/<int:pk>/', DetailView.as_view(),name='task_detail'),
    path('logs/', ExecutionLogListView.as_view(), name='log-list'),
]