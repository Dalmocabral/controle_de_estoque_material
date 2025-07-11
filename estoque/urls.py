from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomLoginView  # Importe a nova view

urlpatterns = [
    path('', CustomLoginView.as_view(), name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),  # Remova os parâmetros extras
    path('dashboard/cadastrar-colaborador/', views.cadastrar_colaborador, name='cadastrar_colaborador'),
]