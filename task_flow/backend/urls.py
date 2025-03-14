from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from backend.views import CreateTaskView, DetailView, ExecutionLogListView

urlpatterns = [
    path('tasks/', CreateTaskView.as_view(),name='task_create'),
    path('tasks/<int:pk>/', DetailView.as_view(),name='task_detail'),
    path('logs/', ExecutionLogListView.as_view(), name='log-list'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
]