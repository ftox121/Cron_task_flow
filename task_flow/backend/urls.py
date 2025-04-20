from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    CheckAndRunTasksView,
    SendDailyNewsletterView,
    BackupDatabaseView,
    CheckInactiveUsersView,
    ClearCacheView
)
from backend.views import TaskViewSet, DetailView, ExecutionLogListView

urlpatterns = [
    path('tasks/', TaskViewSet.as_view({'get': 'list', 'post': 'create'}), name='task_list'),
    path('tasks/<int:pk>/', TaskViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}),
         name='task_detail'),
    path('logs/', ExecutionLogListView.as_view(), name='log-list'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),

    path('check-and-run-tasks/', CheckAndRunTasksView.as_view(), name='check-and-run-tasks'),
    path('send-daily-newsletter/', SendDailyNewsletterView.as_view(), name='send-daily-newsletter'),
    path('backup-database/', BackupDatabaseView.as_view(), name='backup-database'),
    path('check-inactive-users/', CheckInactiveUsersView.as_view(), name='check-inactive-users'),
    path('clear-cache/', ClearCacheView.as_view(), name='clear-cache'),

]
