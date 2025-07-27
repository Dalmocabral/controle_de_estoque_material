from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomLoginView

urlpatterns = [
    # ====================== AUTENTICAÇÃO ======================
    path('', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # ====================== DASHBOARD PRINCIPAL ======================
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # ====================== MÓDULO DE COLABORADORES ======================
    path('dashboard/colaboradores/', views.listar_colaboradores, name='listar_colaboradores'),
    path('dashboard/colaboradores/cadastrar/', views.cadastrar_colaborador, name='cadastrar_colaborador'),
    path('dashboard/colaboradores/editar/<int:pk>/', views.editar_colaborador, name='editar_colaborador'),
    path('dashboard/colaboradores/excluir/<int:pk>/', views.excluir_colaborador, name='excluir_colaborador'),
    
    # ====================== MÓDULO DE EQUIPAMENTOS ======================
    path('dashboard/equipamentos/', views.listar_equipamentos, name='listar_equipamentos'),
    path('dashboard/equipamentos/cadastrar/', views.cadastrar_equipamento, name='cadastrar_equipamento'),
    path('dashboard/equipamentos/detalhe/<int:pk>/', views.detalhe_equipamento, name='detalhe_equipamento'),
    path('dashboard/equipamentos/editar/<int:pk>/', views.editar_equipamento, name='editar_equipamento'),
    path('dashboard/equipamentos/excluir/<int:pk>/', views.excluir_equipamento, name='excluir_equipamento'),
    
    # ====================== ESTOQUE E INVENTÁRIO ======================
    path('dashboard/estoque/resumido/', views.estoque_resumido, name='estoque_resumido'),
    path('dashboard/estoque/detalhado/<str:nome_equipamento>/', views.estoque_detalhado, name='estoque_detalhado'),
    
    # ====================== QR CODE ======================
    path('qrcode/ler/', views.ler_qrcode, name='ler_qrcode'),
    
    # ====================== MÓDULO DE AGENDAMENTOS ======================
    path('dashboard/agendamentos/', views.lista_agendamento_view, name='lista_agendamento'),
    path('dashboard/agendamentos/cadastrar/', views.agendar_view, name='agendar_view'),
    path('dashboard/agendamentos/sucesso/<str:numero>/', views.sucesso_agendamento, name='sucesso_agendamento'),
    path('dashboard/agendamentos/detalhe/<int:pk>/', views.agendamento_detalhe, name='agendamento_detalhe'),
    path('dashboard/agendamentos/editar/<int:pk>/', views.editar_agendamento, name='editar_agendamento'),
    path('dashboard/agendamentos/excluir/<int:pk>/', views.excluir_agendamento, name='excluir_agendamento'),
    
    # ====================== MÓDULO DE SAÍDAS/DEVOLUÇÕES ======================
    path('dashboard/movimentacoes/saidas/', views.lista_saidas, name='lista_saidas'),
    path('dashboard/movimentacoes/saidas/cadastrar/', views.saida_material, name='saida_material'),
    path('dashboard/movimentacoes/saidas/detalhe/<int:pk>/', views.detalhe_saida, name='detalhe_saida'),
    path('dashboard/movimentacoes/saidas/editar/<int:pk>/', views.editar_saida, name='editar_saida'),
    path('dashboard/movimentacoes/saidas/excluir/<int:pk>/', views.excluir_saida, name='excluir_saida'),
    path('dashboard/movimentacoes/devolucao/', views.devolucao_material, name='devolucao_material'),
    
    # ====================== APIs E ENDPOINTS AUXILIARES ======================
    path('api/buscar-pecas/', views.buscar_pecas_com_certificado, name='buscar_pecas_com_certificado'),
    path('api/equipamento/<int:pk>/verificar-agendamentos/', views.verificar_agendamentos_equipamento, name='verificar_agendamentos_equipamento'),
    path('autocomplete/equipamento/', views.autocomplete_equipamento, name='autocomplete_equipamento'),
    path('dashboard/inventario/registrar/<int:pk>/', views.registrar_inventario, name='registrar_inventario'),
    path('dashboard/inventario/problemas/', views.inventario_problemas, name='inventario_problemas'),
    path('dashboard/inventario/detalhe/<int:pk>/', views.inventario_detalhe, name='inventario_detalhe'),
    path('dashboard/inventario/<int:pk>/remover/', views.remover_peca_estoque, name='remover_peca_estoque'),
    path('dashboard/inventario/<int:pk>/', views.inventario_detalhe, name='inventario_detalhe'),
    path('dashboard/relatorios/inventario/', views.relatorio_inventario_pdf, name='relatorio_inventario_pdf'),

    


]