from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
import qrcode
from io import BytesIO
from django.core.files import File
from django.db import models
from django.utils.timezone import now
from django.urls import reverse
import qrcode
import uuid
import random

class Colaborador(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    matricula = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    cpf = models.CharField(
        max_length=14,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$',
                message='CPF deve estar no formato: 000.000.000-00'
            )
        ]
    )
    data_criacao = models.DateTimeField(default=timezone.now)  # Correção aqui
    
    AREA_CHOICES = [
        ('OP', 'Operações'),
        ('ARM', 'Armazém'),
        ('MAT', 'Materiais'),
        ('MANU', 'Manutenção'),
    ]
    
    CARGO_CHOICES = [
        ('GER', 'Gerente'),
        ('CORD', 'Coordenador'),
        ('SUP', 'Supervisor'),
        ('OPR1', 'Operador I'),
        ('OPR2', 'Operador II'),
        ('AUX', 'Auxiliar'),
    ]
    
    area = models.CharField(max_length=6, choices=AREA_CHOICES)
    cargo = models.CharField(max_length=6, choices=CARGO_CHOICES)
    
    def save(self, *args, **kwargs):
        # Formata o nome com iniciais maiúsculas
        self.nome = ' '.join(word.capitalize() for word in self.nome.split())
        if not self.data_criacao:  # Se não tiver data de criação
            self.data_criacao = timezone.now()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nome} ({self.matricula})"
    
    


# Crienado modelo de registro de equipamentos junto com QR Code


def caminho_foto(instance, filename):
    return f'equipamentos/fotos/{filename}'

def caminho_qrcode(instance, filename):
    return f'equipamentos/qrcodes/{filename}'

def caminho_anexo(instance, filename):
    return f'equipamentos/anexos/{filename}'

class Equipamento(models.Model):
    registro = models.AutoField(primary_key=True)  # número único automático
    equipamento = models.CharField(max_length=100)
    identificador = models.CharField(max_length=50)
    caracteristica = models.TextField(blank=True, null=True)
    descricao_uso = models.TextField(blank=True, null=True)

    TIPO_CHOICES = [
        ('ELETRICO', 'Elétrico'),
        ('MANUAL', 'Manual'),
        ('HIDRAULICO', 'Hidráulico'),
        ('PNEUMATICO', 'Pneumático'),
        ('OUTRO', 'Outro'),
    ]
    tipo_equipamento = models.CharField(max_length=20, choices=TIPO_CHOICES)

    quantidade = models.PositiveIntegerField(default=1)
    localizacao = models.CharField(max_length=100)
    foto = models.ImageField(upload_to=caminho_foto, null=True, blank=True)
    qrcode = models.ImageField(upload_to=caminho_qrcode, blank=True)
    data_cadastro = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.equipamento} ({self.identificador})"

    def get_absolute_url(self):
        return reverse('detalhe_equipamento', args=[str(self.pk)])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        qr_data = f"{self.get_absolute_url()}"
        qr = qrcode.make(qr_data)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        file_name = f'qrcode_{self.registro}.png'
        self.qrcode.save(file_name, File(buffer), save=False)

        super().save(*args, **kwargs)

class Certificacao(models.Model):
    equipamento = models.ForeignKey(Equipamento, on_delete=models.CASCADE, related_name='certificacoes')
    nome_certificado = models.CharField(max_length=100)  # Ex: ISO 9001
    data_certificacao = models.DateField()
    data_vencimento = models.DateField(null=True, blank=True)
    empresa_certificadora = models.CharField(max_length=100)
    codigo_certificado = models.CharField(max_length=50)
    detalhes = models.TextField(blank=True, null=True)
    anexo = models.FileField(upload_to='certificacoes/', null=True, blank=True)

    def __str__(self):
        return f"{self.nome_certificado} - {self.equipamento}"
    
    



class Agendamento(models.Model):
    SETOR_CHOICES = [
        ('OPERACOES', 'Operações'),
        ('ARMAZEM', 'Armazém'),
        ('MANUTENCAO', 'Manutenção'),
        ('TERMINAL2', 'Terminal 2'),
    ]
    
    STATUS_CHOICES = [
        ('AG', 'Agendado'),  # Status inicial quando criado
        ('RT', 'Retirado'),  # Quando os materiais são retirados
        ('DV', 'Devolvido'),  # Quando os materiais são devolvidos
        ('CN', 'Cancelado'),  # Quando o agendamento é cancelado
    ]
    
    numero_agendamento = models.CharField(max_length=10, unique=True, blank=True)
    nome_solicitante = models.CharField(max_length=100)
    matricula = models.CharField(max_length=50)
    data_hora_agendamento = models.DateTimeField()
    setor_solicitante = models.CharField(
        max_length=100,
        choices=SETOR_CHOICES,
        default='OPERACOES'
    )
    local_uso = models.TextField()
    tipo_operacao = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=2,
        choices=STATUS_CHOICES,
        default='AG'  # Valor padrão 'Agendado'
    )

    def gerar_numero_agendamento(self):
        while True:
            numero = str(random.randint(1, 99999)).zfill(5)
            if not Agendamento.objects.filter(numero_agendamento=numero).exists():
                self.numero_agendamento = numero
                break

    def save(self, *args, **kwargs):
        if not self.numero_agendamento:
            self.gerar_numero_agendamento()
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"Agendamento {self.numero_agendamento} - {self.nome_solicitante} ({self.get_status_display()})"


class PecaAgendada(models.Model):
    agendamento = models.ForeignKey(Agendamento, on_delete=models.CASCADE, related_name='pecas_agendadas')
    equipamento = models.ForeignKey('Equipamento', on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.equipamento} no {self.agendamento}"
    
    
class SaidaMaterial(models.Model):
    agendamento = models.OneToOneField(
        'Agendamento',
        on_delete=models.PROTECT,
        related_name='saida_material'
    )
    # Remova o campo responsavel_entrega pois usaremos os dados do agendamento
    data_registro = models.DateTimeField(auto_now_add=True)
    observacoes = models.TextField(blank=True)
    termo_assinado = models.FileField(
        upload_to='termos_saida/%Y/%m/%d/',
        null=True,
        blank=True
    )

    @property
    def nome_responsavel(self):
        return self.agendamento.nome_solicitante

    @property
    def matricula_responsavel(self):
        return self.agendamento.matricula

    class Meta:
        verbose_name = 'Saída de Material'
        verbose_name_plural = 'Saídas de Materiais'
        ordering = ['-data_registro']

    def __str__(self):
        return f"Saída #{self.id} - Agendamento {self.agendamento.numero_agendamento}"

class VerificacaoPeca(models.Model):
    saida = models.ForeignKey(
        SaidaMaterial,
        on_delete=models.CASCADE,
        related_name='verificacoes'
    )
    peca = models.ForeignKey(
        'PecaAgendada',
        on_delete=models.PROTECT,
        related_name='verificacoes'
    )
    tem_avaria = models.BooleanField(default=False)
    na_validade = models.BooleanField(default=True)
    tem_certificacao = models.BooleanField(default=True)
    observacao = models.TextField(blank=True)
    foto_avaria = models.ImageField(
        upload_to='avarias/%Y/%m/%d/',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Verificação de Peça'
        verbose_name_plural = 'Verificações de Peças'

    def __str__(self):
        status = "OK"
        if self.tem_avaria or not self.na_validade or not self.tem_certificacao:
            status = "COM PROBLEMAS"
        return f"Verificação {self.peca.id} - {status}"
    
class ChecklistSaida(models.Model):
    saida = models.OneToOneField(SaidaMaterial, on_delete=models.CASCADE, related_name='checklist')
    alguma_avaria = models.BooleanField(default=False)
    validade_ok = models.BooleanField(default=False)
    certificacao_ok = models.BooleanField(default=False)

    def __str__(self):
        return f"Checklist da Saída #{self.saida.id}"

class TermoRetirada(models.Model):
    saida = models.OneToOneField(SaidaMaterial, on_delete=models.CASCADE, related_name='termo')
    lido = models.BooleanField(default=False)
    assinatura_base64 = models.TextField(blank=True)  # salva a imagem da assinatura

    def __str__(self):
        return f"Termo da Saída #{self.saida.id}"


# models.py
class DevolucaoMaterial(models.Model):
    saida = models.OneToOneField(
        SaidaMaterial,
        on_delete=models.PROTECT,
        related_name='devolucao'
    )
    data_devolucao = models.DateTimeField(auto_now_add=True)
    quantidade_devolvida = models.BooleanField(default=True, verbose_name="Quantidade devolvida completa")
    material_com_avaria = models.BooleanField(default=False, verbose_name="Material com avaria")
    observacoes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Devolução de Material'
        verbose_name_plural = 'Devoluções de Materiais'
        ordering = ['-data_devolucao']

    def __str__(self):
        return f"Devolução #{self.id} - Agendamento {self.saida.agendamento.numero_agendamento}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Atualiza o status do agendamento para "Devolvido"
        self.saida.agendamento.status = 'DV'
        self.saida.agendamento.save()
        
        # Atualiza o estoque dos equipamentos
        if self.quantidade_devolvida:
            for peca in self.saida.agendamento.pecas_agendadas.all():
                peca.equipamento.quantidade += 1
                peca.equipamento.save()