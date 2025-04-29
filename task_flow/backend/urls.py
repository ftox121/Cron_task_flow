from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter

from .views import (
    TaskViewSet,
    ExecutionLogViewSet,
    SystemTasksAPIView,
    TaskStatsAPIView,
    PeriodicTaskViewSet
)

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'logs', ExecutionLogViewSet, basename='log')
router.register(r'periodic-tasks', PeriodicTaskViewSet, basename='periodictask')

urlpatterns = [
    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),

    # System Tasks
    path('system-tasks/<str:task_name>/', SystemTasksAPIView.as_view(), name='system-task'),
    path('system-tasks/', SystemTasksAPIView.as_view(), name='system-tasks-list'),

    # Statistics
    path('stats/', TaskStatsAPIView.as_view(), name='task-stats'),

    # Включаем URLs из router
    path('', include(router.urls)),
]