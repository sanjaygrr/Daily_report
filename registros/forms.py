from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Trabajo, Maquina, Faena, Empresa, PerfilUsuario
import datetime
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm

# ---------------------- FORMULARIO REGISTRO USUARIO ----------------------
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    group = forms.ModelChoiceField(queryset=Group.objects.all(), required=True)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ['username', 'first_name',
                  'last_name', 'email', 'password', 'group']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            user.groups.add(self.cleaned_data['group'])
        return user


class EmpresaForm(forms.ModelForm):
    # Campos para la empresa
    nombre = forms.CharField(max_length=100)
    rut = forms.CharField(max_length=20)
    direccion = forms.CharField(max_length=255)
    logo = forms.ImageField(required=False)  # Hacerlo opcional para facilitar pruebas
    correo_electronico = forms.EmailField()
    numero_telefono = forms.CharField(max_length=20)
    max_faenas = forms.IntegerField(min_value=0, required=False)
    max_usuarios = forms.IntegerField(min_value=0, required=False)
    max_maquinas = forms.IntegerField(min_value=0, required=False)
    
    # Campos para el usuario administrador
    admin_username = forms.CharField(max_length=150, label="Nombre de usuario")
    admin_password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")
    admin_first_name = forms.CharField(max_length=150, label="Nombre")
    admin_last_name = forms.CharField(max_length=150, label="Apellido")
    admin_email = forms.EmailField(label="Correo electrónico")

    class Meta:
        model = Empresa
        fields = ['nombre', 'rut', 'direccion', 'logo', 'correo_electronico', 
                 'numero_telefono', 'max_faenas', 'max_usuarios', 'max_maquinas', 'administrador'] #Se agrega el campo administrador

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['administrador'].queryset = User.objects.filter(groups__name='Admin')
            
    def clean(self):
        super().clean()
        admin_username = self.cleaned_data.get('admin_username')
        admin_email = self.cleaned_data.get('admin_email')

        if User.objects.filter(username=admin_username).exists():
            self.add_error('admin_username', 'El nombre de usuario ya existe')
        if User.objects.filter(email=admin_email).exists():
            self.add_error('admin_email', 'El correo electrónico ya existe')
            
    def save(self, commit=True):
        # Primero guardamos la empresa
        empresa = super().save(commit=False)
        
        if commit:
            empresa.save()
        
        # Creamos el usuario administrador
        admin_user = User.objects.create_user(
            username=self.cleaned_data['admin_username'],
            password=self.cleaned_data['admin_password'],
            first_name=self.cleaned_data['admin_first_name'],
            last_name=self.cleaned_data['admin_last_name'],
            email=self.cleaned_data['admin_email']
        )
        
        # Asignamos el grupo 'Admin' al usuario
        grupo_admin, _ = Group.objects.get_or_create(name='Admin')
        admin_user.groups.add(grupo_admin)
        
        # Asignamos el usuario como administrador de la empresa
        empresa.administrador = admin_user
        empresa.save()
        
        # Creamos el perfil del usuario y lo vinculamos a la empresa
        PerfilUsuario.objects.create(
            usuario=admin_user,
            empresa=empresa,
            es_administrador=True #Se agrega el campo es_administrador
        )
        
        return empresa
# ---------------------- FORMULARIO EDICIÓN DE USUARIO ----------------------
class UserEditForm(forms.ModelForm):
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=True,
        label="Rol",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    empresa = forms.ModelChoiceField(
        queryset=Empresa.objects.all(),
        required=False,
        label="Empresa asignada",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'group', 'empresa']  # Add any other fields you want to edit

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
           self.fields['groups'].queryset = Group.objects.filter(name__in=['Trabajador', 'Supervisor'])
           self.fields['empresa'].queryset = user.empresas_administradas.all()

        if self.instance and self.instance.pk:
            user_groups = self.instance.groups.all()
            if user_groups.exists():
                self.fields['group'].initial = user_groups.first().id

# ---------------------- FORMULARIO MÁQUINA ----------------------
class MaquinaForm(forms.ModelForm):
    class Meta:
        model = Maquina
        fields = ['nombre', 'modelo', 'numero_serie', 'fecha_adquisicion', 'estado', 'empresa']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and not user.is_superuser:
            self.fields['empresa'].queryset = Empresa.objects.filter(administrador=user) #cambiado
# ---------------------- FORMULARIO FAENA ----------------------
class FaenaForm(forms.ModelForm):
    class Meta:
        model = Faena
        fields = ['nombre', 'ubicacion', 'descripcion', 'fecha_inicio', 'fecha_termino_estimada', 'responsable', 'empresa']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and not self.user.is_superuser:
            # Limita las empresas al usuario actual
            self.fields['empresa'].queryset = self.user.empresas_administradas.all()

            # Filtra solo usuarios del grupo "Supervisor"
            supervisores = User.objects.filter(groups__name='Supervisor')

            # Si hay relación m2m con empresas_administradas, filtra por empresas comunes
            if hasattr(User, 'empresas_administradas'):
                supervisores = supervisores.filter(
                    empresas_administradas__in=self.user.empresas_administradas.all()
                ).distinct()

            self.fields['responsable'].queryset = supervisores
# ---------------------- FORMULARIO TRABAJO ----------------------
class TrabajoForm(forms.ModelForm):
    fecha = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'max': timezone.now().date().isoformat(),
                'min': (timezone.now() - datetime.timedelta(days=30)).date().isoformat()
            }
        ),
        initial=timezone.now().date()
    )

    class Meta:
        model = Trabajo
        exclude = ['empresa', 'total_horas', 'creado_por', 'estado', 'fecha_creacion', 'fecha_actualizacion']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and hasattr(self.user, 'empresas_administradas'):
            empresa = self.user.empresas_administradas.first()
            self.fields['faena'].queryset = Faena.objects.filter(empresa=empresa)
            self.fields['maquina'].queryset = Maquina.objects.filter(empresa=empresa)
            self.fields['supervisor'].queryset = User.objects.filter(
                groups__name='Supervisor',
                empresas_administradas=empresa
            )
            self.fields['trabajador'].queryset = User.objects.filter(
                groups__name='Trabajador',
                empresas_administradas=empresa
            )
