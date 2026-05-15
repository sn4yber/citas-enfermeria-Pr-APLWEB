from django.urls import path
from citas.infrastructure.views.appointment_views import (
    AuthRegisterView,
    UsuarioView, MedicoView, DisponibilidadView,
    CitaView, CitaCreateView, CitaDetailView,
    EspecialidadView, EspecialidadDetailView,
    EPSView, EPSDetailView,
    OrdenMedicaView, OrdenMedicaDetailView, AutorizarOrdenView,
    HistoriaClinicaView, HistoriaClinicaDetailView, HistoriaClinicaByCitaView,
)

urlpatterns = [
    path('auth/register/', AuthRegisterView.as_view(), name='register'),

    path('usuarios/', UsuarioView.as_view(), name='usuarios'),
    path('medicos/', MedicoView.as_view(), name='medicos'),
    path('disponibilidad/', DisponibilidadView.as_view(), name='disponibilidad'),

    path('citas/', CitaView.as_view(), name='citas'),
    path('citas/create/', CitaCreateView.as_view(), name='citas-create'),
    path('citas/<int:pk>/', CitaDetailView.as_view(), name='citas-detail'),
    path('citas/<int:pk>/historia/', HistoriaClinicaByCitaView.as_view(), name='cita-historia'),

    path('especialidades/', EspecialidadView.as_view(), name='especialidades'),
    path('especialidades/<int:pk>/', EspecialidadDetailView.as_view(), name='especialidades-detail'),

    path('eps/', EPSView.as_view(), name='eps'),
    path('eps/<int:pk>/', EPSDetailView.as_view(), name='eps-detail'),

    path('ordenes-medicas/', OrdenMedicaView.as_view(), name='ordenes-medicas'),
    path('ordenes-medicas/<int:pk>/', OrdenMedicaDetailView.as_view(), name='ordenes-medicas-detail'),
    path('ordenes-medicas/<int:pk>/autorizar/', AutorizarOrdenView.as_view(), name='ordenes-autorizar'),

    path('historias/', HistoriaClinicaView.as_view(), name='historias'),
    path('historias/<int:pk>/', HistoriaClinicaDetailView.as_view(), name='historias-detail'),
]
