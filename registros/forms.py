# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime
from django.db.models import Q

# Asegúrate de importar todos tus modelos aquí
from .models import Trabajo, Maquina, Faena, Empresa, PerfilUsuario

# ---------------------- FORMULARIO REGISTRO DE USUARIO ----------------------

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")
    group = forms.ModelChoiceField(queryset=Group.objects.all(), required=True, label="Rol")
    # Eliminamos el campo 'empresa' de aquí

    class Meta:
        model = User
        # Eliminamos 'empresa' de los fields del formulario
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'group']
        # Renombramos labels si queremos
        labels = {
            'username': 'RUT',  # Cambiado de 'Nombre de Usuario' a 'RUT'
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'email': 'Correo Electrónico',
        }

    def __init__(self, *args, **kwargs):
        # Obtenemos la empresa determinada por la vista
        self.empresa_asignada = kwargs.pop('empresa', None)
        # Eliminamos 'user' si se pasaba, ya no lo necesitamos aquí
        kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Ya no hay lógica para filtrar el queryset de 'empresa'

    def clean_username(self):
        rut = self.cleaned_data.get('username')
        # Eliminar puntos y guiones para normalizar el formato
        rut_limpio = rut.replace('.', '').replace('-', '')
        
        # Verificar que sea numérico (excepto posible K al final)
        if not (rut_limpio[:-1].isdigit() and (rut_limpio[-1].isdigit() or rut_limpio[-1].upper() == 'K')):
            raise ValidationError("El RUT debe contener solo números y posiblemente 'K' al final.")
        
        return rut

    def clean(self):
        cleaned_data = super().clean()
        # La validación ahora usa la empresa asignada desde la vista
        empresa_seleccionada = self.empresa_asignada

        if empresa_seleccionada:
            if empresa_seleccionada.max_usuarios is not None:
                # Contamos perfiles existentes asociados a esa empresa
                # Nota: Esto asume que cada usuario relevante *tendrá* un PerfilUsuario
                num_usuarios_existentes = PerfilUsuario.objects.filter(empresa=empresa_seleccionada).count()
                max_usuarios_permitidos = empresa_seleccionada.max_usuarios

                # Validar solo si estamos creando (instance no tiene pk)
                # o si estamos editando un usuario *que no pertenece ya* a esta empresa (menos común en este form)
                is_new_or_different_company = True # Asumimos creación
                if self.instance and self.instance.pk:
                     # Si fuera un form de edición, verificaríamos si la empresa cambia
                     # PerfilUsuario.objects.filter(usuario=self.instance, empresa=empresa_seleccionada).exists() ... etc.
                     # Para un form de *registro*, asumimos que siempre es un check de nuevo usuario para esa empresa.
                     pass # Mantenemos is_new_or_different_company = True

                if is_new_or_different_company and num_usuarios_existentes >= max_usuarios_permitidos:
                    raise ValidationError(
                        (f"Se ha alcanzado el límite máximo de {max_usuarios_permitidos} usuarios permitidos para la empresa '{empresa_seleccionada.nombre}'."),
                        code='max_usuarios_excedido'
                    )
        else:
             # Si la vista no pudo determinar una empresa, lanzar error.
             # Esto no debería pasar si la lógica de la vista es correcta.
             raise ValidationError(
                 "No se pudo determinar la empresa para validar el límite de usuarios.",
                 code='no_empresa_for_validation'
            )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save() # Guarda el User primero
            # Asigna el grupo seleccionado
            user.groups.clear()
            user.groups.add(self.cleaned_data['group'])

            # Crea o actualiza el PerfilUsuario usando la empresa asignada
            if self.empresa_asignada:
                PerfilUsuario.objects.update_or_create(
                    usuario=user,
                    # Usamos la empresa que la vista determinó y pasó al form
                    defaults={'empresa': self.empresa_asignada}
                )
            # else: Manejar caso donde no hay empresa? La validación clean debería prevenir esto.

        return user


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
        required=False, # Puede que un usuario no tenga empresa asignada directamente si es superuser
        label="Empresa asignada",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'group', 'empresa']
        labels = {
            'username': 'RUT',  # Cambiado de 'Nombre de Usuario' a 'RUT'
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'email': 'Correo Electrónico',
        }

    def __init__(self, *args, **kwargs):
        request_user = kwargs.pop('user', None) # Renombrado para claridad
        super().__init__(*args, **kwargs)

        # Configuración inicial de QuerySets
        self.fields['group'].queryset = Group.objects.all() # Mostrar todos inicialmente
        self.fields['empresa'].queryset = Empresa.objects.all() # Mostrar todas inicialmente

        # Lógica de filtrado basada en el usuario que edita
        if request_user and not request_user.is_superuser:
             # Limitar grupos que puede asignar
             self.fields['group'].queryset = Group.objects.filter(name__in=['Trabajador', 'Supervisor', 'Admin']) # O los roles que correspondan
             # Limitar empresas que puede asignar
             if hasattr(request_user, 'empresas_administradas'):
                 self.fields['empresa'].queryset = request_user.empresas_administradas.all()
             else:
                  self.fields['empresa'].queryset = Empresa.objects.none()

        # Pre-seleccionar valores para el usuario que se está editando (self.instance)
        if self.instance and self.instance.pk:
            # Pre-seleccionar grupo
            user_groups = self.instance.groups.all()
            if user_groups.exists():
                self.fields['group'].initial = user_groups.first() # Asignar objeto Group

            # Pre-seleccionar empresa (a través del perfil)
            try:
                 # Ajusta 'perfil' si el related_name/accessor es diferente
                 if hasattr(self.instance, 'perfil') and self.instance.perfil:
                      self.fields['empresa'].initial = self.instance.perfil.empresa
            except PerfilUsuario.DoesNotExist:
                 self.fields['empresa'].initial = None

    def clean_username(self):
        rut = self.cleaned_data.get('username')
        # Eliminar puntos y guiones para normalizar el formato
        rut_limpio = rut.replace('.', '').replace('-', '')
        
        # Verificar que sea numérico (excepto posible K al final)
        if not (rut_limpio[:-1].isdigit() and (rut_limpio[-1].isdigit() or rut_limpio[-1].upper() == 'K')):
            raise ValidationError("El RUT debe contener solo números y posiblemente 'K' al final.")
        
        return rut

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            selected_group = self.cleaned_data.get('group')
            selected_empresa = self.cleaned_data.get('empresa')

            # Actualizar grupo
            user.groups.set([selected_group]) if selected_group else user.groups.clear()

            # Actualizar perfil y empresa
            if selected_empresa:
                 PerfilUsuario.objects.update_or_create(
                    usuario=user,
                    defaults={'empresa': selected_empresa}
                 )
            else:
                 # Si no se selecciona empresa, quizás eliminar el perfil o desvincularlo
                 PerfilUsuario.objects.filter(usuario=user).delete()

        return user


# ---------------------- FORMULARIO EMPRESA ----------------------

class EmpresaForm(forms.ModelForm):
    nombre = forms.CharField(max_length=100, label="Nombre Empresa")
    rut = forms.CharField(max_length=20, label="RUT Empresa")
    direccion = forms.CharField(max_length=255, required=False, label="Dirección")
    logo = forms.ImageField(required=False, label="Logo")
    correo_electronico = forms.EmailField(required=False, label="Email Empresa")
    numero_telefono = forms.CharField(max_length=20, required=False, label="Teléfono Empresa")
    max_faenas = forms.IntegerField(min_value=1, required=True, initial=1, label="Max. Faenas")
    max_usuarios = forms.IntegerField(min_value=1, required=True, initial=1, label="Max. Usuarios")
    max_maquinas = forms.IntegerField(min_value=1, required=True, initial=1, label="Max. Máquinas")

    admin_username = forms.CharField(max_length=150, label="Admin: RUT")  # Cambiado
    admin_password = forms.CharField(widget=forms.PasswordInput, label="Admin: Contraseña")
    admin_first_name = forms.CharField(max_length=150, required=False, label="Admin: Nombre")
    admin_last_name = forms.CharField(max_length=150, required=False, label="Admin: Apellido")
    admin_email = forms.EmailField(label="Admin: Correo electrónico")

    class Meta:
        model = Empresa
        # Excluimos 'administrador' y 'fecha_creacion' para evitar problemas
        exclude = ['administrador', 'fecha_creacion', 'activa']

    def clean_admin_username(self):
        rut = self.cleaned_data.get('admin_username')
        # Verificar si el RUT ya existe
        if User.objects.filter(username=rut).exists():
            raise ValidationError('El RUT del administrador ya existe.')
        
        # Validar formato RUT
        rut_limpio = rut.replace('.', '').replace('-', '')
        if not (rut_limpio[:-1].isdigit() and (rut_limpio[-1].isdigit() or rut_limpio[-1].upper() == 'K')):
            raise ValidationError("El RUT debe contener solo números y posiblemente 'K' al final.")
        
        return rut

    def clean_admin_email(self):
        email = self.cleaned_data.get('admin_email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('El correo electrónico del administrador ya existe.')
        return email

    def save(self, commit=True):
        empresa = super().save(commit=False)
        
        # Asignar explícitamente la fecha de creación
        empresa.fecha_creacion = timezone.now()

        # Crear usuario admin primero para poder asignarlo a la empresa si es necesario
        try:
            admin_user = User.objects.create_user(
                username=self.cleaned_data['admin_username'],
                password=self.cleaned_data['admin_password'],
                first_name=self.cleaned_data['admin_first_name'],
                last_name=self.cleaned_data['admin_last_name'],
                email=self.cleaned_data['admin_email']
            )
            grupo_admin, _ = Group.objects.get_or_create(name='Admin')
            admin_user.groups.add(grupo_admin)
        except Exception as e:
            raise e

        # Asignar el administrador a la empresa
        empresa.administrador = admin_user

        if commit:
            empresa.save()

            # Crear el perfil del usuario y vincularlo a la empresa
            perfil_defaults = {'empresa': empresa}
            if hasattr(PerfilUsuario, 'es_administrador'):
                perfil_defaults['es_administrador'] = True

            PerfilUsuario.objects.update_or_create(
                usuario=admin_user,
                defaults=perfil_defaults
            )

            # Añadir la empresa a las empresas administradas por el usuario admin
            if hasattr(admin_user, 'empresas_administradas'):
                admin_user.empresas_administradas.add(empresa)

        return empresa

class EmpresaEditForm(forms.ModelForm):
    class Meta:
        model = Empresa
        # Incluye todos los campos que quieres editar, EXCEPTO 'administrador'
        # y los campos 'admin_*' que estaban en EmpresaForm
        fields = [
            'nombre', 'rut', 'direccion', 'logo', 'correo_electronico',
            'numero_telefono', 'max_faenas', 'max_usuarios', 'max_maquinas'
        ]
        # Puedes añadir widgets si necesitas personalizarlos
        widgets = {
            'max_faenas': forms.NumberInput(attrs={'min': '0'}),
            'max_usuarios': forms.NumberInput(attrs={'min': '0'}),
            'max_maquinas': forms.NumberInput(attrs={'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si el logo no es obligatorio al editar
        self.fields['logo'].required = False

    # No necesitas método save() aquí, el de ModelForm es suficiente
    # No necesitas método clean() aquí a menos que tengas validaciones extra
# ---------------------- FORMULARIO MÁQUINA ----------------------

class MaquinaForm(forms.ModelForm):
    class Meta:
        model = Maquina
        # Eliminamos 'estado' y 'empresa' de los campos visibles/editables
        fields = ['nombre', 'modelo', 'numero_serie', 'fecha_adquisicion']
        widgets = {
            'fecha_adquisicion': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            # Puedes añadir clases a otros widgets si quieres mejorar el estilo
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        # Obtenemos la empresa que la vista ha determinado y la quitamos de kwargs
        self.empresa_asignada = kwargs.pop('empresa', None)
        # Quitamos 'user' de kwargs si estaba, ya no lo usamos aquí directamente
        kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Ya no es necesaria la lógica que ajustaba el queryset o initial de 'empresa'

    def clean(self):
        cleaned_data = super().clean()

        # Validación del límite de máquinas usando la empresa asignada por la vista
        if self.empresa_asignada:
            if self.empresa_asignada.max_maquinas is not None:
                # Validar solo al crear una nueva máquina (cuando no hay instancia o no tiene pk)
                if not self.instance or not self.instance.pk:
                    num_maquinas_existentes = Maquina.objects.filter(empresa=self.empresa_asignada).count()
                    max_maquinas_permitidas = self.empresa_asignada.max_maquinas

                    if num_maquinas_existentes >= max_maquinas_permitidas:
                        raise ValidationError(
                            (f"Se ha alcanzado el límite máximo de {max_maquinas_permitidas} "
                             f"máquinas permitidas para la empresa '{self.empresa_asignada.nombre}'."),
                            code='max_maquinas_excedido'
                        )
        else:
            # Si la vista no pasó una empresa (no debería ocurrir con la lógica de la vista), error.
            raise ValidationError(
                "No se pudo determinar la empresa para la validación.",
                code='no_empresa_for_validation'
            )

        # Validaciones propias del modelo (como fechas) que no dependen de los campos eliminados
        # Si tuvieras más validaciones que dependieran de 'estado' o 'empresa' seleccionada,
        # tendrías que adaptarlas o eliminarlas.

        return cleaned_data

# ---------------------- FORMULARIO FAENA ----------------------

class FaenaForm(forms.ModelForm):
    class Meta:
        model = Faena
        # Quitamos 'empresa' de los campos del formulario
        fields = ['nombre', 'ubicacion', 'descripcion', 'fecha_inicio',
                  'fecha_termino_estimada', 'responsable']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_termino_estimada': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
             # Añadir clases a otros widgets si se desea
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'responsable': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = { # Opcional: mejorar etiquetas
            'fecha_termino_estimada': 'Fecha Término Estimada',
            'responsable': 'Supervisor Responsable',
        }

    def __init__(self, *args, **kwargs):
        # Obtenemos la empresa determinada por la vista
        self.empresa_asignada = kwargs.pop('empresa', None)
        # Quitamos 'user' si se pasaba
        kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # --- Filtrar el queryset de 'responsable' ---
        # Basado en la empresa única asignada (pasada desde la vista)
        if self.empresa_asignada:
            self.fields['responsable'].queryset = User.objects.filter(
                groups__name='Supervisor', # Asume que el responsable es del grupo 'Supervisor'
                # Asume que el Supervisor tiene un PerfilUsuario vinculado a la empresa
                perfil__empresa=self.empresa_asignada
            ).distinct().order_by('username') # Ordenar alfabéticamente
        else:
            # Si no hay empresa asignada (no debería pasar si la vista funciona bien),
            # dejar el queryset vacío.
            self.fields['responsable'].queryset = User.objects.none()

        # Ya no necesitamos la lógica para el campo 'empresa' que fue eliminado

    def clean_fecha_termino_estimada(self):
        # Ejemplo de validación limpia para un campo específico
        fecha_inicio = self.cleaned_data.get('fecha_inicio')
        fecha_termino = self.cleaned_data.get('fecha_termino_estimada')
        if fecha_inicio and fecha_termino and fecha_termino < fecha_inicio:
            raise ValidationError("La fecha de término estimada no puede ser anterior a la fecha de inicio.")
        return fecha_termino

    def clean(self):
        cleaned_data = super().clean()
        # Usamos la empresa asignada por la vista para validar max_faenas
        empresa_seleccionada = self.empresa_asignada

        if empresa_seleccionada:
            # Validar límite de faenas si está definido en el modelo Empresa
            if hasattr(empresa_seleccionada, 'max_faenas') and empresa_seleccionada.max_faenas is not None:
                # Validar solo al crear (sin instancia o sin pk)
                if not self.instance or not self.instance.pk:
                    num_faenas_existentes = Faena.objects.filter(empresa=empresa_seleccionada).count()
                    max_faenas_permitidas = empresa_seleccionada.max_faenas

                    if num_faenas_existentes >= max_faenas_permitidas:
                        raise ValidationError(
                            (f"Se ha alcanzado el límite máximo de {max_faenas_permitidas} faenas permitidas para la empresa '{empresa_seleccionada.nombre}'."),
                            code='max_faenas_excedido'
                        )
        else:
            # Esto no debería ocurrir si la vista funciona correctamente
             raise ValidationError(
                 "No se pudo determinar la empresa para validar el límite de faenas.",
                 code='no_empresa_for_validation'
            )

        # Validar que el responsable pertenezca a la empresa asignada
        responsable = cleaned_data.get('responsable')
        if responsable and self.empresa_asignada:
             # Verificar si el perfil del responsable pertenece a la empresa
             if not hasattr(responsable, 'perfil') or responsable.perfil.empresa != self.empresa_asignada:
                  raise ValidationError({
                      'responsable': f"El usuario '{responsable.username}' no es un Supervisor válido para la empresa '{self.empresa_asignada.nombre}'."
                  })

        return cleaned_data
# ---------------------- FORMULARIO TRABAJO ----------------------

class TrabajoForm(forms.ModelForm):
    fecha = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'max': timezone.now().date().isoformat(),
                'min': (timezone.now() - datetime.timedelta(days=30)).date().isoformat() # Límite de 30 días
            }
        ),
        initial=timezone.now().date()
    )

    # Forzar que trabajador sea requerido en el formulario
    trabajador = forms.ModelChoiceField(
        queryset=User.objects.none(), # Se llenará en __init__
        required=True,
        label="Trabajador"
    )

    class Meta:
        model = Trabajo
        # Excluimos campos que se calculan o asignan automáticamente o no deben ser editables aquí
        exclude = ['empresa', 'total_horas', 'creado_por', 'estado',
                   'fecha_creacion', 'fecha_actualizacion']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) # El usuario logueado
        super().__init__(*args, **kwargs)

        # Inicializa querysets vacíos como buena práctica
        self.fields['faena'].queryset = Faena.objects.none()
        self.fields['maquina'].queryset = Maquina.objects.none()
        self.fields['supervisor'].queryset = User.objects.none()
        self.fields['trabajador'].queryset = User.objects.none() # Reinicializa el queryset definido arriba

        if user:
            empresa = None
            # Determinar empresa del usuario logueado
            if hasattr(user, 'perfil') and user.perfil:
                 empresa = user.perfil.empresa

            if user.is_superuser:
                # Superuser: ve todo
                self.fields['faena'].queryset = Faena.objects.all()
                self.fields['maquina'].queryset = Maquina.objects.all()
                self.fields['supervisor'].queryset = User.objects.filter(groups__name='Supervisor')
                # Trabajador puede ser cualquiera en el grupo Trabajador O cualquier Supervisor
                self.fields['trabajador'].queryset = User.objects.filter(
                    Q(groups__name='Trabajador') | Q(groups__name='Supervisor')
                ).distinct()

            elif empresa:
                 # Usuario normal: filtra por su empresa
                self.fields['faena'].queryset = Faena.objects.filter(empresa=empresa)
                self.fields['maquina'].queryset = Maquina.objects.filter(empresa=empresa)
                self.fields['supervisor'].queryset = User.objects.filter(
                    groups__name='Supervisor',
                    perfil__empresa=empresa
                )

                # Queryset para Trabajador: Incluye Trabajadores de la empresa Y Supervisores de la empresa
                trabajadores_empresa = User.objects.filter(groups__name='Trabajador', perfil__empresa=empresa)
                supervisores_empresa = self.fields['supervisor'].queryset # Ya filtrado por empresa
                self.fields['trabajador'].queryset = (trabajadores_empresa | supervisores_empresa).distinct()

                # Preselecciona al trabajador SI el usuario logueado está en el queryset final de trabajador
                # Esto cubre tanto al Trabajador logueado como al Supervisor logueado
                if user in self.fields['trabajador'].queryset:
                     self.fields['trabajador'].initial = user

            # Si no es superuser y no tiene empresa (vía perfil), los querysets quedan vacíos

    def clean(self):
        cleaned_data = super().clean()
        horometro_inicial = cleaned_data.get('horometro_inicial')
        horometro_final = cleaned_data.get('horometro_final')
        trabajador = cleaned_data.get('trabajador')
        supervisor = cleaned_data.get('supervisor')

        if horometro_inicial is not None and horometro_final is not None:
             if horometro_final < horometro_inicial:
                  self.add_error('horometro_final', 'El horómetro/kilometraje final no puede ser menor que el inicial.')

        # La validación del modelo Trabaja.clean() se ejecutará también
        # y verificará la pertenencia a la empresa, etc.

        return cleaned_data

    def save(self, commit=True):
        trabajo = super().save(commit=False)
        horometro_inicial = self.cleaned_data.get('horometro_inicial')
        horometro_final = self.cleaned_data.get('horometro_final')

        if horometro_inicial is not None and horometro_final is not None:
             trabajo.total_horas = horometro_final - horometro_inicial
        else:
             trabajo.total_horas = None

        # La asignación de empresa y la actualización del horómetro de máquina
        # ocurren en el save() del modelo, por lo que no se necesita aquí.

        if commit:
            trabajo.save()
            self.save_m2m() # Necesario si el form tuviera M2M
        return trabajo