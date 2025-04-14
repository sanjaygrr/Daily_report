from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db import IntegrityError
from django.utils import timezone
from django.http import HttpResponse, HttpResponseForbidden
from django.db.models import Q
from .models import Trabajo, Maquina, Faena, Empresa, User, PerfilUsuario
from .forms import (TrabajoForm, MaquinaForm, FaenaForm,
                   UserRegistrationForm, UserEditForm, EmpresaForm)
from .filters import TrabajoFilter
import openpyxl
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import tempfile
from django.conf import settings
from reportlab.lib.units import inch
from reportlab.lib import colors
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.models import Group
from django.core.paginator import Paginator


def get_user_empresa(user):
    # Si es superusuario, no tiene empresa asignada directamente
    if user.is_superuser:
        return None  # O podrías retornar una empresa por defecto o una lista completa

    # Si el usuario es administrador de una o más empresas (relación inversa con related_name)
    if hasattr(user, 'empresas_administradas'):
        empresas_admin = user.empresas_administradas.all()
        if empresas_admin.exists():
            return empresas_admin.first()

    # Si el usuario tiene un perfil con empresa asignada (opcional)
    if hasattr(user, 'perfil') and hasattr(user.perfil, 'empresa'):
        return user.perfil.empresa

    return None


def get_empresa_queryset(user):
    if user.is_superuser:
        return Empresa.objects.all()
    return user.empresas_administradas.all()  # Corrección aquí


def get_maquina_queryset(user):
    empresa = get_user_empresa(user)
    if user.is_superuser:
        return Maquina.objects.all()
    return Maquina.objects.filter(empresa=empresa) if empresa else Maquina.objects.none()


@login_required
def eliminar_maquina(request, pk):
    """
    Vista para eliminar una máquina existente
    """
    maquina = get_object_or_404(Maquina, pk=pk)
    empresa = get_user_empresa(request.user)

    # Verificar permisos
    if not (request.user.is_superuser or maquina.empresa == empresa):
        return HttpResponseForbidden("No tienes permiso para eliminar esta máquina")

    if request.method == 'POST':
        try:
            maquina.delete()
            messages.success(request, 'Máquina eliminada exitosamente!')
            return redirect('listar_maquinas')
        except Exception as e:
            messages.error(request, f'Error al eliminar máquina: {str(e)}')
            return redirect('listar_maquinas')

    return render(request, 'registros/confirmar_eliminar_maquina.html', {
        'maquina': maquina
    })


def get_faena_queryset(user):
    empresa = get_user_empresa(user)
    if user.is_superuser:
        return Faena.objects.all()
    return Faena.objects.filter(empresa=empresa) if empresa else Faena.objects.none()


@login_required
def eliminar_faena(request, pk):
    """
    Vista para eliminar una faena existente
    """
    faena = get_object_or_404(Faena, pk=pk)
    empresa = get_user_empresa(request.user)

    # Verificar permisos
    if not (request.user.is_superuser or faena.empresa == empresa):
        return HttpResponseForbidden("No tienes permiso para eliminar esta faena")

    if request.method == 'POST':
        try:
            faena.delete()
            messages.success(request, 'Faena eliminada exitosamente!')
            return redirect('listar_faenas')
        except Exception as e:
            messages.error(request, f'Error al eliminar faena: {str(e)}')
            return redirect('listar_faenas')

    return render(request, 'registros/confirmar_eliminar_faena.html', {
        'faena': faena
    })


@login_required
def editar_faena(request, pk):
    """
    Vista para editar una faena existente
    """
    faena = get_object_or_404(Faena, pk=pk)
    empresa = get_user_empresa(request.user)

    # Verificar permisos
    if not (request.user.is_superuser or faena.empresa == empresa):
        return HttpResponseForbidden("No tienes permiso para editar esta faena")

    if request.method == 'POST':
        # Corrección: Pasar request.user a FaenaForm
        form = FaenaForm(request.POST, user=request.user, instance=faena)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Faena actualizada exitosamente!')
                return redirect('listar_faenas')
            except IntegrityError as e:
                messages.error(request, f'Error al actualizar faena: {str(e)}')
    else:
        # Corrección: Pasar request.user a FaenaForm
        form = FaenaForm(instance=faena, user=request.user)

    return render(request, 'registros/editar_faena.html', {
        'form': form,
        'faena': faena
    })


def get_trabajo_queryset(user):
    empresa = get_user_empresa(user)
    if user.is_superuser:
        return Trabajo.objects.all()
    return Trabajo.objects.filter(empresa=empresa) if empresa else Trabajo.objects.none()


# Vistas de Empresa
@login_required
def crear_empresa(request):
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES, user=request.user) # Pass the user
        if form.is_valid():
            try:
                empresa = form.save()
                messages.success(request, f'Empresa {empresa.nombre} creada exitosamente con su administrador!')
                return redirect('listar_empresas')
            except Exception as e:
                messages.error(request, f'Error al crear empresa: {str(e)}')
        else:
            # Si hay errores de validación, los mostraremos
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    else:
        form = EmpresaForm(user=request.user) # Pass the user
    return render(request, 'registros/crear_empresa.html', {'form': form})



@login_required
def listar_empresas(request):
    empresas = get_empresa_queryset(request.user)
    paginator = Paginator(empresas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'registros/listar_empresas.html', {'page_obj': page_obj})


@login_required
def editar_empresa(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)

    if not (request.user.is_superuser or request.user == empresa.administrador):
        return HttpResponseForbidden("No tienes permiso para editar esta empresa")

    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES, instance=empresa, user=request.user) # Pass the user
        if form.is_valid():
            form.save()
            messages.success(request, 'Empresa actualizada correctamente')
            return redirect('listar_empresas')
    else:
        form = EmpresaForm(instance=empresa, user=request.user) # Pass the user
    return render(request, 'registros/editar_empresa.html', {'form': form, 'empresa': empresa})


@login_required
def eliminar_empresa(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)

    if not (request.user.is_superuser or request.user == empresa.administrador):
        return HttpResponseForbidden("No tienes permiso para eliminar esta empresa")

    if request.method == 'POST':
        try:
            empresa.delete()
            messages.success(request, 'Empresa eliminada correctamente')
            return redirect('listar_empresas')
        except Exception as e:
            messages.error(request, f'Error al eliminar empresa: {str(e)}')
            return redirect('listar_empresas')

    return render(request, 'registros/confirmar_eliminar_empresa.html', {'empresa': empresa})
# Vistas de Trabajos
@login_required
def crear_trabajo(request):
    empresa = get_user_empresa(request.user)
    if not empresa and not request.user.is_superuser:
        return HttpResponseForbidden("No tienes una empresa asignada")

    if request.method == 'POST':
        # Cambié el argumento para pasar 'user' en lugar de 'empresa'
        form = TrabajoForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                trabajo = form.save(commit=False)
                trabajo.creado_por = request.user
                trabajo.empresa = empresa
                trabajo.save()
                messages.success(request, 'Trabajo creado exitosamente!')
                return redirect('historial')
            except IntegrityError as e:
                messages.error(request, f'Error al crear trabajo: {str(e)}')
                return redirect('crear_trabajo')
    else:
        # También cambié para pasar 'user' en lugar de 'empresa'
        form = TrabajoForm(user=request.user, initial={'fecha': timezone.now().date()})

    return render(request, 'registros/crear_trabajo.html', {'form': form})


@login_required
def historial(request):
    # Verificamos si el usuario es superusuario
    if request.user.is_superuser:
        # Si es superusuario, no filtramos por empresa
        trabajos = get_trabajo_queryset(request.user)
    else:
        # Si no es superusuario, filtramos por empresa
        trabajos = get_trabajo_queryset(request.user)
    f = TrabajoFilter(request.GET, queryset=trabajos)
    paginator = Paginator(f.qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'registros/historial.html', {'filter': f, 'page_obj': page_obj})


@login_required
def pendientes(request):
    trabajos = get_trabajo_queryset(request.user).filter(estado='pendiente')
    paginator = Paginator(trabajos, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'registros/pendientes.html', {'page_obj': page_obj})


@login_required
def aprobar_trabajo(request, pk):
    trabajo = get_object_or_404(Trabajo, pk=pk)

    if not (request.user == trabajo.supervisor or request.user.is_superuser):
        return HttpResponseForbidden("No tienes permiso para aprobar este trabajo")

    try:
        trabajo.estado = 'completado'
        trabajo.save()
        messages.success(request, 'Trabajo aprobado exitosamente!')
    except Exception as e:
        messages.error(request, f'Error al aprobar trabajo: {str(e)}')

    return redirect('pendientes')


@login_required
def register_user(request):
    empresa = get_user_empresa(request.user)

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, user=request.user)  # se pasa user como keyword
        if form.is_valid():
            try:
                user = form.save()
                messages.success(request, f'Usuario creado exitosamente!')
                return redirect('listar_usuarios')
            except IntegrityError as e:
                messages.error(request, f'Error al crear usuario: {str(e)}')
                return redirect('register_user')
    else:
        form = UserRegistrationForm(user=request.user)

    return render(request, 'registros/register_user.html', {'form': form})


@login_required
def listar_usuarios(request):
    empresa = get_user_empresa(request.user)

    if request.user.is_superuser:
        usuarios = User.objects.all()
    else:
        usuarios = User.objects.filter(Q(perfil__empresa=empresa))  # Filtra usuarios por empresa a través del perfil

    paginator = Paginator(usuarios, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    forms = {}
    for usuario in page_obj.object_list:
        forms[usuario.pk] = UserEditForm(instance=usuario, user=request.user)

    if request.method == 'POST':
        usuario_id = request.POST.get('usuario_id')
        if usuario_id:
            usuario = get_object_or_404(User, pk=usuario_id)
            form = UserEditForm(request.POST, instance=usuario, user=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Usuario actualizado exitosamente!')
                return redirect('listar_usuarios')

    return render(request, 'registros/listar_usuarios.html', {
        'page_obj': page_obj,
        'forms': forms
    })


@login_required
def eliminar_usuario(request, pk):
    """
    Vista para eliminar un usuario
    """
    usuario = get_object_or_404(User, pk=pk)
    empresa = get_user_empresa(request.user)

    # Verificar permisos
    if not (request.user.is_superuser or usuario.perfil.empresa == empresa): # Access empresa via perfil
        return HttpResponseForbidden("No tienes permiso para eliminar este usuario")

    if request.method == 'POST':
        try:
            usuario.delete()
            messages.success(request, 'Usuario eliminado exitosamente!')
            return redirect('listar_usuarios')
        except Exception as e:
            messages.error(request, f'Error al eliminar usuario: {str(e)}')
            return redirect('listar_usuarios')

    return render(request, 'registros/confirmar_eliminar_usuario.html', {
        'usuario': usuario
    })


@login_required
def guardar_cambios_usuarios(request):
    """
    Vista para guardar cambios múltiples de usuarios
    """
    if request.method == 'POST':
        try:
            # Obtener todos los usuarios de la empresa del administrador
            empresa = get_user_empresa(request.user)
            if request.user.is_superuser:
                usuarios = User.objects.all()
            else:
                usuarios = User.objects.filter(perfil__empresa=empresa) # Access empresa via perfil

            # Procesar cada usuario
            for usuario in usuarios:
                usuario_id = str(usuario.id)
                form = UserEditForm(request.POST, prefix=usuario_id, instance=usuario,
                                   user=request.user)
                if form.is_valid():
                    form.save()

            messages.success(request, 'Cambios en usuarios guardados exitosamente!')
        except Exception as e:
            messages.error(request, f'Error al guardar cambios: {str(e)}')

        return redirect('listar_usuarios')

    return HttpResponseForbidden("Método no permitido")


# Vistas de Máquinas
@login_required
def crear_maquina(request):
    empresa = get_user_empresa(request.user)
    if not empresa and not request.user.is_superuser:
        return HttpResponseForbidden("No tienes una empresa asignada")

    if request.method == 'POST':
        form = MaquinaForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                maquina = form.save(commit=False)
                maquina.empresa = empresa
                maquina.save()
                messages.success(request, 'Máquina creada exitosamente!')
                return redirect('listar_maquinas')
            except IntegrityError as e:
                messages.error(request, f'Error al crear máquina: {str(e)}')
                return redirect('crear_maquina')
    else:
        form = MaquinaForm(user=request.user)  # Pass user here

    return render(request, 'registros/crear_maquina.html', {'form': form})

@login_required
def listar_maquinas(request):
    maquinas = get_maquina_queryset(request.user)
    paginator = Paginator(maquinas, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    forms = {maquina.pk: MaquinaForm(instance=maquina, user=request.user) for maquina in page_obj.object_list}

    if request.method == 'POST':
        maquina_id = request.POST.get('maquina_id')
        if maquina_id:
            maquina = get_object_or_404(Maquina, pk=maquina_id)
            form = MaquinaForm(request.POST, instance=maquina, user=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Máquina actualizada exitosamente!')
                return redirect('listar_maquinas')

    return render(request, 'registros/listar_maquinas.html', {
        'page_obj': page_obj,
        'forms': forms
    })


# Vistas de Faenas
@login_required
def crear_faena(request):
    empresa = get_user_empresa(request.user)
    if not empresa and not request.user.is_superuser:
        return HttpResponseForbidden("No tienes una empresa asignada")

    if request.method == 'POST':
        form = FaenaForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                faena = form.save(commit=False)
                faena.empresa = empresa
                faena.save()
                messages.success(request, 'Faena creada exitosamente!')
                return redirect('listar_faenas')
            except IntegrityError as e:
                messages.error(request, f'Error al crear faena: {str(e)}')
                return redirect('crear_faena')
    else:
        form = FaenaForm(user=request.user)

    return render(request, 'registros/crear_faena.html', {'form': form})


@login_required
def listar_faenas(request):
    faenas = get_faena_queryset(request.user)
    paginator = Paginator(faenas, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    forms = {faena.pk: FaenaForm(instance=faena, user=request.user) for faena in page_obj.object_list}

    if request.method == 'POST':
        faena_id = request.POST.get('faena_id')
        if faena_id:
            faena = get_object_or_404(Faena, pk=faena_id)
            form = FaenaForm(request.POST, instance=faena, user=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Faena actualizada exitosamente!')
                return redirect('listar_faenas')

    return render(request, 'registros/listar_faenas.html', {
        'page_obj': page_obj,
        'forms': forms
    })


# Exportación y reportes
@login_required
def export_historial_xlsx(request):
    trabajos = get_trabajo_queryset(request.user)
    filter_trabajos = TrabajoFilter(request.GET, queryset=trabajos)
    trabajos = filter_trabajos.qs

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    empresa = get_user_empresa(request.user)
    filename = f"Historial_Trabajos_{empresa.nombre.replace(' ', '_')}" if empresa else "Historial_Trabajos"
    response['Content-Disposition'] = f'attachment; filename={filename}.xlsx'

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'Historial de Trabajos'

    columns = [
        'Empresa', 'Fecha', 'Faena', 'Máquina', 'Trabajo',
        'Horómetro Inicial', 'Horómetro Final', 'Total Horas',
        'Petróleo (lts)', 'Aceite (tipo)', 'Aceite (lts)', 'Observaciones',
        'Supervisor', 'Trabajador', 'Estado'
    ]

    for col_num, column_title in enumerate(columns, 1):
        column_letter = get_column_letter(col_num)
        cell = worksheet[f"{column_letter}1"]
        cell.value = column_title
        cell.font = openpyxl.styles.Font(bold=True)

    row_num = 2
    for trabajo in trabajos:
        worksheet.append([
            trabajo.empresa.nombre if trabajo.empresa else '',
            trabajo.fecha,
            trabajo.faena.nombre,
            trabajo.maquina.nombre,
            trabajo.trabajo,
            float(trabajo.horometro_inicial),
            float(trabajo.horometro_final),
            float(trabajo.total_horas) if trabajo.total_horas else 0,
            float(trabajo.petroleo_litros),
            trabajo.aceite_tipo,
            float(trabajo.aceite_litros),
            trabajo.observaciones,
            trabajo.supervisor.get_full_name() or trabajo.supervisor.username,
            trabajo.trabajador.get_full_name() or trabajo.trabajador.username,
            trabajo.estado.capitalize()
        ])
        row_num += 1

    for column in worksheet.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        for cell in column:
            try:
                max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        adjusted_width = (max_length + 2) * 1.2
        worksheet.column_dimensions[column_letter].width = adjusted_width

    workbook.save(response)
    return response


@login_required
def generar_pdf_trabajo(request, pk):
    trabajo = get_object_or_404(Trabajo, pk=pk)
    user_empresa = get_user_empresa(request.user)

    if not (request.user.is_superuser or user_empresa == trabajo.empresa):
        return HttpResponseForbidden("No tienes permiso para ver este trabajo")

    response = HttpResponse(content_type='application/pdf')
    filename = f"Reporte_{trabajo.faena.nombre}_{trabajo.fecha}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Estilos
    titulo_style = ("Helvetica-Bold", 16)
    subtitulo_style = ("Helvetica-Bold", 12)
    texto_style = ("Helvetica", 10)

    # Logo de la empresa
    logo = None
    if trabajo.empresa and trabajo.empresa.logo:
        try:
            logo_file = default_storage.open(trabajo.empresa.logo.name)
            with tempfile.NamedTemporaryFile(delete=False) as temp_logo:
                temp_logo.write(logo_file.read())
                logo = temp_logo.name
        except Exception as e:
            print(f"Error al cargar logo: {str(e)}")

    if logo and os.path.exists(logo):
        p.drawImage(logo, width - 2 * inch, height - 1 * inch,
                    width=1.5 * inch, height=1 * inch, preserveAspectRatio=True)
        os.unlink(logo)

    # Encabezado
    p.setFont(*titulo_style)
    p.drawString(1 * inch, height - 1.5 * inch, "Reporte de Trabajo")

    if trabajo.empresa:
        p.setFont(*subtitulo_style)
        p.drawString(1 * inch, height - 2 * inch, f"Empresa: {trabajo.empresa.nombre}")
        p.drawString(1 * inch, height - 2.2 * inch, f"RUT: {trabajo.empresa.rut}")

    p.line(1 * inch, height - 2.5 * inch, width - 1 * inch, height - 2.5 * inch)

    y_position = height - 3 * inch
    p.setFont(*subtitulo_style)
    p.drawString(1 * inch, y_position, "Detalles del Trabajo:")

    p.setFont(*texto_style)
    detalles = [
        ("Fecha", trabajo.fecha.strftime("%d/%m/%Y")),
        ("Faena", trabajo.faena.nombre),
        ("Máquina", f"{trabajo.maquina.nombre} ({trabajo.maquina.modelo})"),
        ("Trabajo realizado", trabajo.trabajo),
        ("Tipo de Medida", trabajo.tipo_medida),
        ("Horómetro Inicial", f"{trabajo.horometro_inicial} {trabajo.tipo_medida}"),
        ("Horómetro Final", f"{trabajo.horometro_final} {trabajo.tipo_medida}"),
        ("Total", f"{trabajo.total_horas} {trabajo.tipo_medida}"),
        ("Petróleo", f"{trabajo.petroleo_litros} litros"),
        ("Aceite", f"{trabajo.aceite_tipo} ({trabajo.aceite_litros} litros)"),
        ("Supervisor", trabajo.supervisor.get_full_name()),
        ("Trabajador", trabajo.trabajador.get_full_name()),
        ("Estado", trabajo.get_estado_display())
    ]

    col1_x = 1 * inch
    col2_x = 4.5 * inch
    line_height = 0.4 * inch

    for i, (label, value) in enumerate(detalles):
        x = col1_x if i % 2 == 0 else col2_x
        y = y_position - (i // 2 + 1) * line_height - 0.2 * inch
        p.drawString(x, y, f"{label}:")
        p.drawString(x + 1.5 * inch, y, str(value))

    y_position -= (len(detalles) // 2 + 2) * line_height
    p.setFont(*subtitulo_style)
    p.drawString(1 * inch, y_position, "Observaciones:")
    p.setFont(*texto_style)
    observaciones = trabajo.observaciones or "Sin observaciones"
    p.drawString(1 * inch, y_position - line_height, observaciones)

    p.setFont("Helvetica", 8)
    p.drawString(1 * inch, 0.5 * inch, f"Generado el {timezone.now().strftime('%d/%m/%Y %H:%M')} por {request.user.get_full_name()}")

    p.showPage()
    p.save()
    return response


# Vistas generales
def home(request):
    context = {}
    if request.user.is_authenticated:
        # Obtenemos el perfil del usuario y la empresa asociada a él
        perfil_usuario = getattr(request.user, 'perfil',
                                 None)  # Accede al perfil del usuario
        empresa = perfil_usuario.empresa if perfil_usuario else None

        context.update({
            'empresa': empresa,
            'es_administrador': request.user.groups.filter(name='Admin').exists(),
            'es_supervisor': request.user.groups.filter(name='Supervisor').exists()
        })

        if empresa and empresa.logo:
            context['logo_empresa'] = empresa.logo.url

    return render(request, 'registros/home.html', context)


@login_required
def detalle_empresa(request, pk):
    """
    Vista para ver los detalles completos de una empresa incluyendo
    estadísticas de usuarios, máquinas y faenas
    """
    empresa = get_object_or_404(Empresa, pk=pk)

    # Obtenemos conteos y detalles
    usuarios = User.objects.filter(
        Q(perfil__empresa=empresa))  # Corrección para filtrar por la empresa del perfil
    maquinas = Maquina.objects.filter(empresa=empresa)
    faenas = Faena.objects.filter(empresa=empresa)
    trabajos = Trabajo.objects.filter(empresa=empresa)

    estadisticas = {
        'total_usuarios': usuarios.count(),
        'usuarios_por_grupo': {
            'Admin': usuarios.filter(groups__name='Admin').count(),
            'Supervisor': usuarios.filter(groups__name='Supervisor').count(),
            'Trabajador': usuarios.filter(groups__name='Trabajador').count(),
        },
        'total_maquinas': maquinas.count(),
        'total_faenas': faenas.count(),
        'total_trabajos': trabajos.count(),
        'trabajos_por_estado': {
            'completados': trabajos.filter(estado='completado').count(),
            'pendientes': trabajos.filter(estado='pendiente').count(),
        }
    }

    return render(request, 'registros/detalle_empresa.html', {
        'empresa': empresa,
        'estadisticas': estadisticas,
        'usuarios': usuarios,
        'maquinas': maquinas,
        'faenas': faenas,
    })
