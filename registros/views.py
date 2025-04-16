# views.py
import openpyxl
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
import os
import tempfile
import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import IntegrityError
from django.utils import timezone
from django.http import HttpResponse, HttpResponseForbidden
from django.db.models import Q, Count, Prefetch
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.exceptions import MultipleObjectsReturned, ValidationError

from .models import Trabajo, Maquina, Faena, Empresa, PerfilUsuario # Asegúrate que PerfilUsuario esté aquí
from .forms import (
    TrabajoForm, MaquinaForm, FaenaForm, UserRegistrationForm,
    UserEditForm, EmpresaForm, EmpresaEditForm
)
from .filters import TrabajoFilter # Asegúrate que este filtro exista

# ---------------------- HELPERS ----------------------
def get_user_empresa(user):
    """
    Obtiene la única empresa asociada a un usuario no superusuario.
    Prioriza 'empresas_administradas' y luego 'perfil.empresa'.
    Devuelve la instancia de Empresa si es única.
    Devuelve None si no hay empresa o es superusuario.
    Lanza MultipleObjectsReturned si se encuentran múltiples empresas administradas.
    """
    if user.is_superuser:
        return None

    # 1. Intenta obtener desde 'empresas_administradas' (prioridad)
    if hasattr(user, 'empresas_administradas'):
        empresas_admin = user.empresas_administradas.all()
        count = empresas_admin.count()

        if count == 1:
            # Caso ideal: administra exactamente una empresa
            return empresas_admin.first()
        elif count > 1:
            # Administra múltiples empresas: hay ambigüedad
            raise MultipleObjectsReturned(f"El usuario {user.username} administra {count} empresas.")
        # Si count es 0, continúa para verificar el perfil

    # 2. Si no se encontró una única en 'empresas_administradas', intenta desde el perfil
    if hasattr(user, 'perfil') and user.perfil and hasattr(user.perfil, 'empresa') and user.perfil.empresa:
        # Asume que la relación perfil-empresa implica una única empresa
        return user.perfil.empresa

    # 3. Si no se encontró empresa por ninguna vía
    return None
# ---------------------- VISTAS GENERALES ----------------------

def home(request):
    context = {}
    if request.user.is_authenticated:
        perfil_usuario = getattr(request.user, 'perfil', None)
        empresa = perfil_usuario.empresa if perfil_usuario else None
        context.update({
            'empresa': empresa,
            'es_administrador': request.user.groups.filter(name='Admin').exists(),
            'es_supervisor': request.user.groups.filter(name='Supervisor').exists()
        })
        if empresa and empresa.logo:
            context['logo_empresa'] = empresa.logo.url
    return render(request, 'registros/home.html', context)

# ---------------------- VISTAS DE EMPRESA ----------------------

@login_required
#@user_passes_test(lambda u: u.is_superuser) # O permiso específico
def crear_empresa(request):
    if not request.user.is_superuser:
         messages.error(request, "Solo los superusuarios pueden crear empresas.")
         return redirect('home') # O a donde corresponda

    if request.method == 'POST':
        # No se pasa 'user' aquí, EmpresaForm maneja la creación del admin
        form = EmpresaForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                empresa = form.save()
                messages.success(request, f'Empresa {empresa.nombre} creada exitosamente con su administrador!')
                return redirect('listar_empresas')
            except Exception as e:
                messages.error(request, f'Error al crear empresa: {str(e)}')
                # Considera añadir errores específicos del formulario si es necesario
                # Por ejemplo, si la creación del usuario falla dentro de form.save()
        else:
            # Mostrar errores de validación
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field if field != "__all__" else "General"}: {error}')
    else:
        form = EmpresaForm()
    return render(request, 'registros/crear_empresa.html', {'form': form})

@login_required
#@user_passes_test(lambda u: u.is_superuser)
def listar_empresas(request):
    if not request.user.is_superuser:
         messages.error(request, "Solo los superusuarios pueden listar empresas.")
         return redirect('home')

    empresas_list = Empresa.objects.all().order_by('nombre')
    paginator = Paginator(empresas_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'registros/listar_empresas.html', {'page_obj': page_obj})

@login_required
#@user_passes_test(lambda u: u.is_superuser) # Asegúrate que solo SU pueda editar
def editar_empresa(request, pk):
    if not request.user.is_superuser:
        messages.error(request, "Solo los superusuarios pueden editar empresas.")
        return redirect('home')

    empresa = get_object_or_404(Empresa, pk=pk)

    if request.method == 'POST':
        # Usa el nuevo formulario de edición
        form = EmpresaEditForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save() # Guarda los cambios en la empresa (incluidos los límites)
            messages.success(request, f'Empresa "{empresa.nombre}" actualizada correctamente.')
            return redirect('listar_empresas') # Vuelve a la lista
        else:
            # Muestra errores de validación específicos
            for field, errors in form.errors.items():
                for error in errors:
                    # Muestra el error en la página de la lista, ya que el modal se cierra
                    messages.error(request, f'Error al actualizar {empresa.nombre} - {field if field != "__all__" else "General"}: {error}')
            # Redirige de vuelta a la lista para mostrar los mensajes de error
            # Idealmente, se podría usar AJAX para mantener el modal abierto y mostrar errores,
            # pero esta es la solución más simple sin AJAX.
            return redirect('listar_empresas')
    else:
        # Para GET (aunque no se usa si todo es por modal), preparamos el form
        # Si quisieras una página de edición separada, aquí usarías EmpresaEditForm
        # form = EmpresaEditForm(instance=empresa)
        # return render(request, 'registros/editar_empresa.html', {'form': form, 'empresa': empresa})
        # Como usamos modal, la petición GET no debería llegar a esta vista separada
        # Redirigir si se intenta acceder por GET podría ser una opción
        messages.warning(request, "La edición se realiza a través del modal en la lista.")
        return redirect('listar_empresas')
    
@login_required
@require_POST # Para consistencia con modal (si se implementa)
#@user_passes_test(lambda u: u.is_superuser)
def eliminar_empresa(request, pk):
    if not request.user.is_superuser:
         messages.error(request, "Solo los superusuarios pueden eliminar empresas.")
         return redirect('home')

    empresa = get_object_or_404(Empresa, pk=pk)
    try:
        empresa_nombre = empresa.nombre
        # Considerar qué pasa con usuarios, máquinas, etc., al eliminar la empresa
        # Podrías necesitar eliminar o desasociar objetos relacionados primero
        empresa.delete()
        messages.success(request, f'Empresa "{empresa_nombre}" eliminada correctamente')
    except Exception as e:
        messages.error(request, f'Error al eliminar empresa: {str(e)}')

    return redirect('listar_empresas')

login_required
#@user_passes_test(lambda u: u.is_superuser) # Puedes descomentar si solo superuser debe entrar
def detalles_empresa(request, pk): # Asegúrate que tu URL use 'pk' si usas pk aquí
    if not request.user.is_superuser:
        messages.error(request, "Solo los superusuarios pueden ver detalles de empresas.")
        return redirect('home')

    empresa = get_object_or_404(Empresa, pk=pk)

    # Calcular roles de usuario
    user_roles = (
        User.objects
        .filter(perfil__empresa=empresa) # Asume relación User -> PerfilUsuario (perfil) -> Empresa (empresa)
        .values('groups__name') # Asume relación User -> Group (groups)
        .annotate(user_count=Count('id'))
        .order_by('groups__name')
    )

    # Calcular conteos
    maquina_count = Maquina.objects.filter(empresa=empresa).count()
    faena_count = Faena.objects.filter(empresa=empresa).count()
    trabajo_count = Trabajo.objects.filter(empresa=empresa).count()

    # Crear el diccionario de contexto COMPLETO
    context = {
        'empresa': empresa,
        'user_roles': user_roles,
        'maquina_count': maquina_count,
        'faena_count': faena_count,
        'trabajo_count': trabajo_count,
        # --- LÍNEAS AÑADIDAS ---
        'max_usuarios': empresa.max_usuarios,
        'max_faenas': empresa.max_faenas,
        'max_maquinas': empresa.max_maquinas,
        # --- FIN LÍNEAS AÑADIDAS ---
    }
    # Renderizar la plantilla con el contexto actualizado
    return render(request, 'registros/detalles_empresa.html', context)

# ---------------------- VISTAS DE USUARIO ----------------------

@login_required
def register_user(request):
    empresa_del_registrador = None

    # --- Determinar la empresa del usuario que registra ---
    try:
        # Permitimos Superuser Y Admin/Supervisor (según tu lógica de permisos)
        # Pero solo asignamos empresa automáticamente si NO es Superuser
        if request.user.is_superuser:
             # Decisión: ¿Permitir a SU registrar sin asignar empresa? ¿O bloquear?
             # Bloquearemos esta vista para SU, deben usar admin u otra interfaz.
             messages.error(request, "Los Superusuarios deben usar la interfaz de administración para crear usuarios y asignar empresas.")
             return redirect('home') # O redirect('admin:index')

        # Para Admin/Supervisor, obtenemos su (única) empresa
        empresa_del_registrador = get_user_empresa(request.user)

        if not empresa_del_registrador:
             messages.error(request, "No se pudo determinar una única empresa asociada a tu cuenta para asignar al nuevo usuario.")
             return redirect('home') # O a donde corresponda

    except MultipleObjectsReturned:
         messages.error(request, "Administras múltiples empresas. No puedes registrar usuarios automáticamente desde aquí.")
         return redirect('home')
    except Exception as e:
         messages.error(request, f"Error al determinar tu empresa: {e}")
         return redirect('home')

    # --- Lógica de Permisos (Ya la tenías, la mantenemos) ---
    # Asegurarse que solo usuarios permitidos accedan (Admin o Supervisor en este caso)
    # Nota: El chequeo de SU ya se hizo arriba para la lógica de la empresa.
    if not request.user.groups.filter(name__in=['Admin', 'Supervisor']).exists():
        # Si llegamos aquí, no es SU y tampoco Admin/Supervisor
        messages.error(request, "No tienes permiso para registrar usuarios.")
        return redirect('home')

    # Si llegamos aquí, empresa_del_registrador tiene la empresa única del Admin/Supervisor

    if request.method == 'POST':
        # Pasamos la empresa determinada al formulario, quitamos user=request.user
        form = UserRegistrationForm(request.POST, empresa=empresa_del_registrador)
        if form.is_valid():
            try:
                # El método save del form ahora maneja la asignación al PerfilUsuario
                user = form.save()
                messages.success(request, f'Usuario {user.username} creado exitosamente en la empresa {empresa_del_registrador.nombre}!')
                 # Ajusta 'listar_usuarios' al nombre de tu URL
                return redirect('listar_usuarios')
            except IntegrityError as e:
                 # Capturar error de username duplicado, etc.
                 if 'UNIQUE constraint failed: auth_user.username' in str(e):
                      messages.error(request, f"El nombre de usuario '{form.cleaned_data.get('username')}' ya existe.")
                 else:
                      messages.error(request, f'Error de base de datos al crear usuario: {str(e)}')
            except ValidationError as e: # Errores del form.clean (ej: max_usuarios)
                 messages.error(request, f"Error de validación: {e.message}")
            except Exception as e:
                 messages.error(request, f'Error inesperado al crear usuario: {str(e)}')
        else:
            # Ajustamos el mensaje de error general
            messages.error(request, 'No se pudo crear el usuario. Por favor, revisa los campos.')
    else:
        # Pasamos la empresa también para GET
        form = UserRegistrationForm(empresa=empresa_del_registrador)

    # La plantilla 'registros/register_user.html' recibe el form SIN el campo 'empresa'
    return render(request, 'registros/register_user.html', {'form': form})



@login_required
def listar_usuarios(request):
    empresa_actual = get_user_empresa(request.user)
    usuarios_query = User.objects.all()

    if not request.user.is_superuser:
        if empresa_actual:
            # Filtrar por perfil__empresa
            usuarios_query = usuarios_query.filter(perfil__empresa=empresa_actual)
        else:
            # Si no es superuser y no tiene empresa, no debería ver usuarios
            usuarios_query = User.objects.none()

    usuarios_list = usuarios_query.select_related('perfil').prefetch_related(
        'groups',
        'perfil__empresa'
    ).order_by('username')

    paginator = Paginator(usuarios_list, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Pasar los forms para edición en línea si esa es la intención
    # Si no, este diccionario de forms podría no ser necesario
    forms = {}
    # for usuario in page_obj.object_list:
    #     forms[usuario.pk] = UserEditForm(instance=usuario, user=request.user)

    context = {
        'page_obj': page_obj,
        'forms': forms, # Opcional
        'usuarios': page_obj.object_list,
        'groups': Group.objects.all() # Necesario para el dropdown en la tabla
    }
    return render(request, 'registros/listar_usuarios.html', context)

@login_required
@require_POST # Implementando modal
def eliminar_usuario(request, pk):
    usuario_a_eliminar = get_object_or_404(User, pk=pk)
    empresa_actual = get_user_empresa(request.user)

    permiso_para_eliminar = False
    if request.user.is_superuser:
        permiso_para_eliminar = True
    # Verifica si el usuario a eliminar tiene perfil y pertenece a la misma empresa
    elif hasattr(usuario_a_eliminar, 'perfil') and usuario_a_eliminar.perfil and usuario_a_eliminar.perfil.empresa == empresa_actual:
        # Podrías añadir un check extra: ¿es el usuario logueado un Admin?
        if request.user.groups.filter(name='Admin').exists():
             permiso_para_eliminar = True

    if not permiso_para_eliminar:
        messages.error(request, "No tienes permiso para eliminar este usuario.")
        return redirect('listar_usuarios')

    if usuario_a_eliminar == request.user:
         messages.error(request, "No puedes eliminar tu propia cuenta.")
         return redirect('listar_usuarios')

    try:
        username = usuario_a_eliminar.username
        # Eliminar perfil antes que el usuario
        if hasattr(usuario_a_eliminar, 'perfil'):
            try:
                usuario_a_eliminar.perfil.delete()
            except PerfilUsuario.DoesNotExist:
                pass # No había perfil, no hay problema
        usuario_a_eliminar.delete()
        messages.success(request, f'Usuario "{username}" eliminado exitosamente!')
    except Exception as e:
        messages.error(request, f'Error al eliminar usuario "{usuario_a_eliminar.username}": {str(e)}')

    return redirect('listar_usuarios')

@login_required
@require_POST # Esta vista parece diseñada para procesar datos de la tabla editable
def guardar_cambios_usuarios(request):
    # Esta vista necesita lógica más compleja si se usa para editar en línea
    # Se debe iterar sobre los datos POST para identificar qué usuario y qué campo cambiar
    # Por ahora, solo un mensaje y redirección
    messages.info(request, "Funcionalidad 'Guardar Cambios Múltiples' no implementada completamente en la vista.")
    return redirect('listar_usuarios')


# ---------------------- VISTAS DE MÁQUINA ----------------------

@login_required
def crear_maquina(request):
    empresa_asignada = None
    try:
        # --- Lógica para determinar la empresa automáticamente ---
        if request.user.is_superuser:
            messages.error(request, "Los superusuarios no pueden crear máquinas automáticamente. Utilice la interfaz de administración para especificar la empresa.")
            return redirect('home') # O a la vista de lista o admin

        empresa_asignada = get_user_empresa(request.user)

        if not empresa_asignada:
            messages.error(request, "No se encontró una única empresa asociada a su usuario para la asignación automática.")
            return redirect('home') # O a donde corresponda

    except MultipleObjectsReturned:
        messages.error(request, "Usted administra múltiples empresas. No se puede asignar una automáticamente para crear la máquina.")
        return redirect('home') # O a donde corresponda
    except Exception as e:
        messages.error(request, f"Ocurrió un error al determinar su empresa: {e}")
        return redirect('home')

    # Si llegamos aquí, 'empresa_asignada' contiene la única empresa del usuario

    if request.method == 'POST':
        # Pasamos la empresa determinada al formulario en el constructor
        form = MaquinaForm(request.POST, empresa=empresa_asignada)
        if form.is_valid():
            try:
                # Guardamos sin hacer commit para asignar la empresa manualmente
                maquina = form.save(commit=False)
                maquina.empresa = empresa_asignada # Asignamos la empresa
                # El campo 'estado' ya no existe, no hay nada que asignar.
                maquina.save() # Guardamos la instancia completa en la BD
                # form.save_m2m() # Llamar si hubiera campos ManyToMany en el form

                messages.success(request, f'Máquina {maquina.nombre} creada exitosamente para la empresa {empresa_asignada.nombre}!')
                # Ajusta 'listar_maquinas' al nombre real de tu URL
                return redirect('listar_maquinas')
            except IntegrityError as e:
                 # Captura errores como unique_together ('nombre', 'empresa')
                if 'UNIQUE constraint failed' in str(e) and 'maquina_nombre_empresa_id_uniq' in str(e): # Ajusta el nombre de la constraint si es diferente
                     messages.error(request, f"Ya existe una máquina con el nombre '{form.cleaned_data.get('nombre')}' en la empresa '{empresa_asignada.nombre}'.")
                else:
                     messages.error(request, f'Error de base de datos al crear máquina: {str(e)}')
            except ValidationError as e: # Errores del form.clean() como max_maquinas
                 messages.error(request, f"Error de validación: {e.message}")
            except Exception as e:
                messages.error(request, f'Error inesperado al crear máquina: {str(e)}')
        else:
            # Los errores de campo se mostrarán automáticamente por la plantilla
            messages.error(request, 'Error al crear máquina. Por favor, revise los datos ingresados.')
    else:
        # Para GET, también pasamos la empresa (puede ser útil si el form hiciera algo con ella en init)
        form = MaquinaForm(empresa=empresa_asignada)

    # La plantilla ('registros/crear_maquina.html') usará este 'form', que ya no
    # contiene los campos 'estado' ni 'empresa'.
    return render(request, 'registros/crear_maquina.html', {'form': form})

@login_required
def listar_maquinas(request):
    empresa_actual = get_user_empresa(request.user)
    maquinas_query = Maquina.objects.select_related('empresa')

    if not request.user.is_superuser:
        if empresa_actual:
            maquinas_query = maquinas_query.filter(empresa=empresa_actual)
        else:
            maquinas_query = Maquina.objects.none()

    # Obtiene la lista COMPLETA ordenada
    maquinas_list = maquinas_query.order_by('nombre')

    # Obtener choices para el estado (necesario para el modal de edición)
    estado_choices = []
    if hasattr(Maquina, 'ESTADO_CHOICES'): # Comprueba si el atributo existe en el modelo
        estado_choices = Maquina.ESTADO_CHOICES

    # Pasa la lista completa con la clave 'maquinas_list' que espera la plantilla
    context = {
        'maquinas_list': maquinas_list,
        'estado_choices': estado_choices,
    }
    return render(request, 'registros/listar_maquinas.html', context)


# --- Vista Editar Maquina (Maneja POST del modal) ---
@login_required
def editar_maquina(request, pk):
    maquina = get_object_or_404(Maquina, pk=pk)
    empresa_actual = get_user_empresa(request.user)

    permiso_para_editar = False
    if request.user.is_superuser:
         permiso_para_editar = True
    elif maquina.empresa == empresa_actual:
         # Asume Admin o Supervisor pueden editar máquinas de su empresa
         if request.user.groups.filter(name__in=['Admin', 'Supervisor']).exists():
              permiso_para_editar = True

    if not permiso_para_editar:
        messages.error(request,"No tienes permiso para editar esta máquina.")
        return redirect('listar_maquinas')

    if request.method == 'POST':
        # Usa el MaquinaForm normal, pasándole el usuario si el form lo necesita
        form = MaquinaForm(request.POST, instance=maquina, user=request.user)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Máquina "{maquina.nombre}" actualizada exitosamente!')
            except Exception as e:
                 messages.error(request, f'Error al actualizar máquina: {str(e)}')
        else:
             # Captura errores de validación
             error_list = []
             for field, errors in form.errors.items():
                 error_list.append(f'{field}: {", ".join(errors)}')
             messages.error(request, f"No se pudo actualizar la máquina '{maquina.nombre}'. Errores: {'; '.join(error_list)}")

        # Siempre redirige a la lista después de POST
        return redirect('listar_maquinas')
    else:
         # GET request no esperado si se usa modal
        messages.info(request, "Usa el botón 'Editar' en la lista para modificar máquinas.")
        return redirect('listar_maquinas')


@login_required
@require_POST # Implementando modal
def eliminar_maquina(request, pk):
    maquina = get_object_or_404(Maquina, pk=pk)
    empresa_actual = get_user_empresa(request.user)

    permiso_para_eliminar = False
    if request.user.is_superuser:
        permiso_para_eliminar = True
    elif maquina.empresa == empresa_actual:
         # Asumimos que si pertenece a la empresa, puede eliminar (o añadir check de Rol Admin)
         if request.user.groups.filter(name__in=['Admin', 'Supervisor']).exists(): # Ejemplo de permiso
              permiso_para_eliminar = True

    if not permiso_para_eliminar:
        messages.error(request, "No tienes permiso para eliminar esta máquina.")
        return redirect('listar_maquinas')

    try:
        maquina_nombre = maquina.nombre
        maquina.delete()
        messages.success(request, f'Máquina "{maquina_nombre}" eliminada exitosamente!')
    except Exception as e:
        messages.error(request, f'Error al eliminar máquina: {str(e)}')

    return redirect('listar_maquinas')


# ---------------------- VISTAS DE FAENA ----------------------

def get_user_empresa(user):
    # ... (pega aquí la definición de get_user_empresa que ajustamos antes)
    if user.is_superuser:
        return None
    if hasattr(user, 'empresas_administradas'):
        empresas_admin = user.empresas_administradas.all()
        count = empresas_admin.count()
        if count == 1:
            return empresas_admin.first()
        elif count > 1:
            raise MultipleObjectsReturned(f"El usuario {user.username} administra {count} empresas.")
    if hasattr(user, 'perfil') and user.perfil and hasattr(user.perfil, 'empresa') and user.perfil.empresa:
        return user.perfil.empresa
    return None
# --- Fin de get_user_empresa ---

@login_required
def crear_faena(request):
    empresa_asignada = None
    try:
        # --- Determinar la empresa del usuario que crea la faena ---
        if request.user.is_superuser:
             messages.error(request, "Los Superusuarios deben usar la interfaz de administración para crear faenas y asignar empresas.")
             return redirect('home') # O admin

        empresa_asignada = get_user_empresa(request.user)

        if not empresa_asignada:
             messages.error(request, "No se pudo determinar una única empresa asociada a tu cuenta para crear la faena.")
             return redirect('home') # O a listar_faenas, etc.

    except MultipleObjectsReturned:
        messages.error(request, "Administras múltiples empresas. No puedes crear faenas automáticamente desde aquí.")
        return redirect('home')
    except Exception as e:
        messages.error(request, f"Error al determinar tu empresa: {e}")
        return redirect('home')

    # Si llegamos aquí, empresa_asignada contiene la empresa única del usuario

    if request.method == 'POST':
        # Pasamos la empresa determinada al formulario
        form = FaenaForm(request.POST, empresa=empresa_asignada)
        if form.is_valid():
            try:
                # Guardamos sin commit para asignar la empresa manualmente
                faena = form.save(commit=False)
                faena.empresa = empresa_asignada # Asignamos la empresa
                faena.save() # Guardamos la instancia completa
                # form.save_m2m() # Si hubiera campos M2M

                messages.success(request, f'Faena {faena.nombre} creada exitosamente para la empresa {empresa_asignada.nombre}!')
                 # Ajusta 'listar_faenas' al nombre de tu URL
                return redirect('listar_faenas')
            except IntegrityError as e:
                 # Podría haber unique constraints en Faena (ej: nombre+empresa)
                 messages.error(request, f'Error de base de datos al crear faena: {str(e)}')
            except ValidationError as e: # Errores del form.clean (ej: max_faenas, responsable inválido)
                 # Los errores de campo (como el de responsable) se manejan en el form.errors
                 # Mostramos errores no ligados a campos específicos (non_field_errors)
                 if hasattr(e, 'message_dict'): # Errores de campo específico
                      for field, errors in e.message_dict.items():
                           messages.error(request, f"Error en '{form.fields[field].label}': {'; '.join(errors)}")
                 elif hasattr(e, 'message'): # Errores generales (non_field_errors)
                      messages.error(request, f"Error de validación: {e.message}")
                 else:
                     messages.error(request, f"Error de validación: {e}")

            except Exception as e:
                messages.error(request, f'Error inesperado al crear faena: {str(e)}')
        else:
             messages.error(request, 'Error al crear faena. Por favor, revise los datos ingresados.')
             # Los errores específicos de cada campo se mostrarán en la plantilla
             # usando {{ form.campo.errors }} o iterando sobre form.errors.
    else:
        # Pasamos la empresa también para GET (necesario para filtrar 'responsable')
        form = FaenaForm(empresa=empresa_asignada)

    # La plantilla 'registros/crear_faena.html' recibe el form SIN el campo 'empresa'
    return render(request, 'registros/crear_faena.html', {'form': form})

@login_required
def listar_faenas(request):
    empresa_actual = get_user_empresa(request.user)
    # Usamos select_related para optimizar acceso a empresa y responsable
    faenas_query = Faena.objects.select_related('empresa', 'responsable__perfil')

    if not request.user.is_superuser:
        if empresa_actual:
            faenas_query = faenas_query.filter(empresa=empresa_actual)
        else:
            faenas_query = Faena.objects.none()

    # Obtener lista completa ordenada
    faenas_list = faenas_query.order_by('nombre')

    # Obtener lista de supervisores para el modal de edición
    supervisores_list = User.objects.none()
    if request.user.is_superuser:
         supervisores_list = User.objects.filter(groups__name='Supervisor').order_by('username')
    elif empresa_actual:
          supervisores_list = User.objects.filter(
              groups__name='Supervisor',
              perfil__empresa=empresa_actual # Asume relación PerfilUsuario
              ).order_by('username')

    context = {
        # Pasar la lista completa con el nombre 'faenas_list'
        'faenas_list': faenas_list,
        'supervisores_list': supervisores_list, # Necesario para el modal
        # Ya no necesitamos 'page_obj'
    }
    return render(request, 'registros/listar_faenas.html', context)
# --- Vista Editar Faena (Maneja POST del modal) ---
@login_required
def editar_faena(request, pk):
    faena = get_object_or_404(Faena, pk=pk)
    empresa_actual = get_user_empresa(request.user)

    permiso_para_editar = False
    if request.user.is_superuser:
         permiso_para_editar = True
    elif faena.empresa == empresa_actual:
         # Asume Admin o Supervisor pueden editar faenas de su empresa
         if request.user.groups.filter(name__in=['Admin', 'Supervisor']).exists():
              permiso_para_editar = True

    if not permiso_para_editar:
        messages.error(request,"No tienes permiso para editar esta faena.")
        return redirect('listar_faenas')

    if request.method == 'POST':
        # Usa el FaenaForm normal, pasándole el usuario para filtrar el 'responsable' si es necesario
        form = FaenaForm(request.POST, instance=faena, user=request.user)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Faena "{faena.nombre}" actualizada exitosamente!')
            except Exception as e:
                messages.error(request, f'Error al actualizar faena: {str(e)}')
                # Considera mostrar errores del form aquí si es necesario
                # for field, errors in form.errors.items(): ... etc
        else:
             # Captura errores de validación
             error_list = []
             for field, errors in form.errors.items():
                 error_list.append(f'{field}: {", ".join(errors)}')
             messages.error(request, f"No se pudo actualizar la faena '{faena.nombre}'. Errores: {'; '.join(error_list)}")

        # Siempre redirige a la lista después de POST (éxito o fracaso)
        return redirect('listar_faenas')
    else:
        # GET request a esta URL no es esperado si se usa modal
        messages.info(request, "Usa el botón 'Editar' en la lista para modificar faenas.")
        return redirect('listar_faenas')

@login_required
@require_POST # Implementando modal
def eliminar_faena(request, pk):
    faena = get_object_or_404(Faena, pk=pk)
    empresa_actual = get_user_empresa(request.user)

    permiso_para_eliminar = False
    if request.user.is_superuser:
        permiso_para_eliminar = True
    elif faena.empresa == empresa_actual:
         if request.user.groups.filter(name__in=['Admin', 'Supervisor']).exists(): # Ejemplo
              permiso_para_eliminar = True

    if not permiso_para_eliminar:
        messages.error(request, "No tienes permiso para eliminar esta faena.")
        return redirect('listar_faenas')

    try:
        faena_nombre = faena.nombre
        faena.delete()
        messages.success(request, f'Faena "{faena_nombre}" eliminada exitosamente!')
    except Exception as e:
        messages.error(request, f'Error al eliminar faena: {str(e)}')

    return redirect('listar_faenas')


# ---------------------- VISTAS DE TRABAJO ----------------------

@login_required
def crear_trabajo(request):
    empresa_actual = get_user_empresa(request.user)
    puede_crear = request.user.is_superuser or (empresa_actual is not None)

    # Lógica de permisos por rol
    if not request.user.is_superuser and not request.user.groups.filter(name__in=['Admin', 'Supervisor', 'Trabajador']).exists():
         puede_crear = False # Si no tiene rol adecuado

    if not puede_crear:
        messages.error(request,"No tienes permiso o empresa asignada para crear trabajos.")
        return redirect('home')

    if request.method == 'POST':
        form = TrabajoForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                trabajo = form.save(commit=False)
                trabajo.creado_por = request.user
                # Asignar empresa basado en la faena/maquina seleccionada si no se asigna de otra forma
                if not trabajo.empresa:
                     if trabajo.faena:
                          trabajo.empresa = trabajo.faena.empresa
                     elif trabajo.maquina:
                          trabajo.empresa = trabajo.maquina.empresa
                     else: # O asignar la del usuario si es la única forma
                          trabajo.empresa = empresa_actual

                trabajo.save()
                messages.success(request, 'Trabajo creado exitosamente!')
                return redirect('historial') # O a donde corresponda
            except IntegrityError as e:
                messages.error(request, f'Error de base de datos al crear trabajo: {str(e)}')
            except Exception as e:
                messages.error(request, f'Error inesperado al crear trabajo: {str(e)}')
        else:
            messages.error(request, "Error al crear trabajo. Revisa los campos.")
    else:
        # Pasa el usuario para filtrar dropdowns
        form = TrabajoForm(user=request.user, initial={'fecha': timezone.now().date()})

    return render(request, 'registros/crear_trabajo.html', {'form': form})


@login_required
def historial(request):
    trabajos_query = Trabajo.objects.select_related(
        'empresa', 'faena', 'maquina', 'supervisor', 'trabajador'
    )

    if not request.user.is_superuser:
        empresa_actual = get_user_empresa(request.user)
        if empresa_actual:
            trabajos_query = trabajos_query.filter(empresa=empresa_actual)
        else:
            # Si no es SU y no tiene empresa, no ve trabajos
            trabajos_query = Trabajo.objects.none()

    # Aplicar filtros de TrabajoFilter
    trabajo_filter = TrabajoFilter(request.GET, queryset=trabajos_query)

    # Ordenar antes de paginar
    trabajos_ordenados = trabajo_filter.qs.order_by('-fecha', '-id') # Ejemplo de orden

    paginator = Paginator(trabajos_ordenados, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'filter': trabajo_filter,
        'page_obj': page_obj
    }
    return render(request, 'registros/historial.html', context)


@login_required
def pendientes(request):
    trabajos_query = Trabajo.objects.select_related(
        'empresa', 'faena', 'maquina', 'supervisor', 'trabajador'
    ).filter(estado='pendiente') # Asume estado='pendiente'

    # Permisos: ¿Quién ve pendientes? Supervisores de su empresa, Admins, SU?
    if not request.user.is_superuser:
        empresa_actual = get_user_empresa(request.user)
        if empresa_actual and request.user.groups.filter(name__in=['Admin', 'Supervisor']).exists():
             trabajos_query = trabajos_query.filter(empresa=empresa_actual)
             # Supervisor sólo ve los asignados a él?
             # if request.user.groups.filter(name='Supervisor').exists():
             #     trabajos_query = trabajos_query.filter(supervisor=request.user)
        else:
             trabajos_query = Trabajo.objects.none() # Otros roles o sin empresa no ven pendientes


    trabajos_ordenados = trabajos_query.order_by('fecha', 'id') # Ejemplo

    paginator = Paginator(trabajos_ordenados, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'trabajos': page_obj.object_list # Pasar la lista para iterar en template
    }
    return render(request, 'registros/pendientes.html', context)


@login_required
@require_POST # La aprobación debería ser una acción POST
def aprobar_trabajo(request, pk):
    trabajo = get_object_or_404(Trabajo, pk=pk)
    empresa_actual = get_user_empresa(request.user)

    permiso_para_aprobar = False
    if request.user.is_superuser:
         permiso_para_aprobar = True
    # Solo Admin o el Supervisor asignado de la misma empresa pueden aprobar
    elif trabajo.empresa == empresa_actual:
         if request.user.groups.filter(name='Admin').exists() or request.user == trabajo.supervisor:
              permiso_para_aprobar = True

    if not permiso_para_aprobar:
        messages.error(request,"No tienes permiso para aprobar este trabajo")
        return redirect('pendientes') # O a donde corresponda

    if trabajo.estado != 'pendiente':
         messages.warning(request, f"El trabajo ya está en estado '{trabajo.get_estado_display()}'.")
         return redirect('pendientes')

    try:
        # Asume que 'aprobado' es el estado final
        trabajo.estado = 'aprobado' # O 'completado' según tu modelo
        trabajo.save()
        messages.success(request, 'Trabajo aprobado exitosamente!')
    except Exception as e:
        messages.error(request, f'Error al aprobar trabajo: {str(e)}')

    return redirect('pendientes')


# ---------------------- EXPORTACIÓN Y REPORTES ----------------------

@login_required
def export_historial_xlsx(request):
    trabajos_query = Trabajo.objects.select_related(
        'empresa', 'faena', 'maquina', 'supervisor', 'trabajador'
    )

    if not request.user.is_superuser:
        empresa_actual = get_user_empresa(request.user)
        if empresa_actual:
            trabajos_query = trabajos_query.filter(empresa=empresa_actual)
        else:
            trabajos_query = Trabajo.objects.none()

    trabajo_filter = TrabajoFilter(request.GET, queryset=trabajos_query)
    trabajos_filtrados = trabajo_filter.qs.order_by('-fecha', '-id') # Mismo orden que historial

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    empresa_actual = get_user_empresa(request.user) # Obtener de nuevo por si acaso
    filename_base = "Historial_Trabajos"
    if empresa_actual:
         filename = f"{filename_base}_{empresa_actual.nombre.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d')}"
    else:
         filename = f"{filename_base}_{timezone.now().strftime('%Y%m%d')}"
    response['Content-Disposition'] = f'attachment; filename={filename}.xlsx'

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'Historial Trabajos'

    columns = [
        'Empresa', 'Fecha', 'Faena', 'Máquina', 'Trabajo', 'Tipo Medida',
        'H/K Inicial', 'H/K Final', 'Total H/K',
        'Petróleo (lts)', 'Aceite (tipo)', 'Aceite (lts)', 'Observaciones',
        'Supervisor', 'Trabajador', 'Estado'
    ]

    header_font = openpyxl.styles.Font(bold=True)
    for col_num, column_title in enumerate(columns, 1):
        cell = worksheet.cell(row=1, column=col_num, value=column_title)
        cell.font = header_font

    row_num = 2
    for trabajo in trabajos_filtrados:
        # Formatear valores para Excel
        fecha_str = trabajo.fecha.strftime("%d/%m/%Y") if trabajo.fecha else ''
        hk_inicial = float(trabajo.horometro_inicial) if trabajo.horometro_inicial is not None else ''
        hk_final = float(trabajo.horometro_final) if trabajo.horometro_final is not None else ''
        total_hk = float(trabajo.total_horas) if trabajo.total_horas is not None else ''
        petroleo = float(trabajo.petroleo_litros) if trabajo.petroleo_litros is not None else ''
        aceite_lts = float(trabajo.aceite_litros) if trabajo.aceite_litros is not None else ''

        worksheet.append([
            trabajo.empresa.nombre if trabajo.empresa else '',
            fecha_str,
            trabajo.faena.nombre if trabajo.faena else '',
            trabajo.maquina.nombre if trabajo.maquina else '',
            trabajo.trabajo,
            trabajo.tipo_medida,
            hk_inicial,
            hk_final,
            total_hk,
            petroleo,
            trabajo.aceite_tipo,
            aceite_lts,
            trabajo.observaciones,
            trabajo.supervisor.get_full_name() or trabajo.supervisor.username if trabajo.supervisor else '',
            trabajo.trabajador.get_full_name() or trabajo.trabajador.username if trabajo.trabajador else '',
            trabajo.get_estado_display() # Usa el método del modelo si existe
        ])
        row_num += 1 # No es necesario incrementar manualmente con append

    # Ajustar ancho de columnas
    for col_idx in range(1, len(columns) + 1):
         column_letter = get_column_letter(col_idx)
         worksheet.column_dimensions[column_letter].autosize = True

    workbook.save(response)
    return response


@login_required
def generar_pdf_trabajo(request, pk):
    trabajo = get_object_or_404(Trabajo.objects.select_related(
         'empresa', 'faena', 'maquina', 'supervisor', 'trabajador'
         ), pk=pk)
    user_empresa = get_user_empresa(request.user)

    permiso_para_ver = False
    if request.user.is_superuser:
         permiso_para_ver = True
    elif trabajo.empresa == user_empresa:
         # Asume que cualquier usuario de la empresa puede ver el PDF
         permiso_para_ver = True
         # Podrías restringir más por rol si es necesario

    if not permiso_para_ver:
        messages.error(request, "No tienes permiso para generar este reporte.")
        # Redirigir a historial o home podría ser mejor que Forbidden
        return redirect('historial')

    response = HttpResponse(content_type='application/pdf')
    filename = f"Reporte_{trabajo.faena.nombre if trabajo.faena else 'SinFaena'}_{trabajo.fecha.strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"' # inline para ver en navegador

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    margin = inch

    # Logo (manejo seguro de archivos)
    logo_path_temp = None
    if trabajo.empresa and trabajo.empresa.logo:
        try:
            logo_file = default_storage.open(trabajo.empresa.logo.name)
            # Crear archivo temporal seguro
            fd, logo_path_temp = tempfile.mkstemp(suffix=".png") # Asume png o ajusta
            with os.fdopen(fd, 'wb') as temp_logo:
                 temp_logo.write(logo_file.read())
            logo_file.close()
            # Dibujar imagen
            p.drawImage(logo_path_temp, width - margin - 1.5*inch, height - margin - 0.5*inch,
                         width=1.5*inch, height=0.5*inch, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Error al procesar logo para PDF: {e}")
        finally:
            # Asegurar eliminación del archivo temporal
             if logo_path_temp and os.path.exists(logo_path_temp):
                  try:
                       os.unlink(logo_path_temp)
                  except OSError as e:
                       print(f"Error eliminando archivo temporal de logo: {e}")


    # Títulos
    p.setFont("Helvetica-Bold", 16)
    p.drawString(margin, height - margin, "Reporte Diario de Trabajo")

    y_position = height - margin - 0.5*inch
    if trabajo.empresa:
        p.setFont("Helvetica", 10)
        p.drawString(margin, y_position, f"Empresa: {trabajo.empresa.nombre} (RUT: {trabajo.empresa.rut})")
        y_position -= 0.25*inch

    p.line(margin, y_position, width - margin, y_position)
    y_position -= 0.4*inch

    # Datos del trabajo
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y_position, "Detalles del Registro:")
    y_position -= 0.3*inch

    data = [
        ("Fecha:", trabajo.fecha.strftime("%d/%m/%Y") if trabajo.fecha else "N/A"),
        ("Faena:", trabajo.faena.nombre if trabajo.faena else "N/A"),
        ("Máquina:", trabajo.maquina.nombre if trabajo.maquina else "N/A"),
        ("Modelo:", trabajo.maquina.modelo if trabajo.maquina else "N/A"),
        ("Trabajo Realizado:", trabajo.trabajo),
        ("Tipo Medida:", trabajo.tipo_medida),
        (f"{trabajo.tipo_medida} Inicial:", trabajo.horometro_inicial),
        (f"{trabajo.tipo_medida} Final:", trabajo.horometro_final),
        (f"Total {trabajo.tipo_medida}:", trabajo.total_horas),
        ("Petróleo (Lts):", trabajo.petroleo_litros),
        ("Tipo Aceite:", trabajo.aceite_tipo),
        ("Aceite (Lts):", trabajo.aceite_litros),
        ("Supervisor:", trabajo.supervisor.get_full_name() if trabajo.supervisor else "N/A"),
        ("Trabajador:", trabajo.trabajador.get_full_name() if trabajo.trabajador else "N/A"),
        ("Estado:", trabajo.get_estado_display()),
    ]

    p.setFont("Helvetica", 10)
    line_height_pdf = 0.25 * inch
    max_label_width = 2 * inch # Ancho para etiquetas
    value_start_x = margin + max_label_width + 0.2*inch

    for label, value in data:
         p.drawString(margin, y_position, label)
         p.drawString(value_start_x, y_position, str(value))
         y_position -= line_height_pdf
         # Salto de página si es necesario (simplificado)
         if y_position < margin * 1.5:
              p.showPage()
              y_position = height - margin # Reiniciar Y en nueva página

    # Observaciones
    y_position -= 0.2*inch # Espacio extra
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y_position, "Observaciones:")
    y_position -= 0.3*inch
    p.setFont("Helvetica", 10)
    # Manejo de texto largo para observaciones
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    observaciones_text = trabajo.observaciones if trabajo.observaciones else "Sin observaciones."
    obs_paragraph = Paragraph(observaciones_text, styleN)
    w_obs, h_obs = obs_paragraph.wrapOn(p, width - 2*margin, height) # Ancho disponible
    obs_paragraph.drawOn(p, margin, y_position - h_obs)
    y_position -= (h_obs + 0.2*inch)


    # Pie de página
    p.setFont("Helvetica", 8)
    p.drawCentredString(width / 2.0, margin * 0.5, f"Reporte generado el {timezone.now().strftime('%d/%m/%Y %H:%M')} por {request.user.get_full_name()}")

    p.showPage()
    p.save()
    return response