from django.urls import path
from citas.infrastructure.views.appointment_views import (
    AuthRegisterView,
    UsuarioView, CitaView, CitaCreateView, CitaDetailView,
    EspecialidadView, EspecialidadDetailView
)

urlpatterns = [
    path('auth/register/', AuthRegisterView.as_view(), name='register'),
    
    path('usuarios/', UsuarioView.as_view(), name='usuarios'),
    
    path('citas/', CitaView.as_view(), name='citas'),
    path('citas/create/', CitaCreateView.as_view(), name='citas-create'),
    path('citas/<int:pk>/', CitaDetailView.as_view(), name='citas-detail'),
    
    path('especialidades/', EspecialidadView.as_view(), name='especialidades'),
    path('especialidades/<int:pk>/', EspecialidadDetailView.as_view(), name='especialidades-detail'),
]