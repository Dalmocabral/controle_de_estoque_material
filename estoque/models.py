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
    
    
  