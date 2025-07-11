from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomLoginView  # Importe a nova view

urlpatterns = [
    path('', CustomLoginView.as_view(), name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),  # Remova os parâmetros extras
    path('dashboard/cadastrar-colaborador/', views.cadastrar_colaborador, name='cadastrar_colaborador'),
    path('dashboard/colaboradores/', views.listar_colaboradores, name='listar_colaboradores'),
    
    
    path('dashboard/colaboradores/editar/<int:pk>/', views.editar_colaborador, name='editar_colaborador'),
    path('dashboard/colaboradores/excluir/<int:pk>/', views.excluir_colaborador, name='excluir_colaborador'),
    
    path('dashboard/equipamentos/detalhe_equipamento/<int:pk>/', views.detalhe_equipamento, name='detalhe_equipamento'),
    path('dashboard/equipamentos/cadastrar/', views.cadastrar_equipamento, name='cadastrar_equipamento'),
    path('dashboard/equipamentos/listar_equipamentos', views.listar_equipamentos, name='listar_equipamentos'),
    path('qrcode/ler/', views.ler_qrcode, name='ler_qrcode'),
    path('dashboard/equipamentos/estoque/', views.estoque_resumido, name='estoque_resumido'),
    path('autocomplete/equipamento/', views.autocomplete_equipamento, name='autocomplete_equipamento'),
    
]