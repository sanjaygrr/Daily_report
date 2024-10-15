from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Trabajo, Maquina, Faena
from .forms import TrabajoForm, MaquinaForm, FaenaForm, UserRegistrationForm
from .filters import TrabajoFilter
from django.utils import timezone
from django.http import HttpResponse
import openpyxl
from openpyxl.utils import get_column_letter
from django.contrib.auth.models import User
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from reportlab.lib.units import inch
from reportlab.lib import colors

from django.http import HttpResponseForbidden
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def admin_view(request):
    return redirect('/admin/')


def home(request):
    context = {}
    if request.user.is_authenticated:
        context['username'] = request.user.username
    return render(request, 'registros/home.html', context)


@login_required
def crear_trabajo(request):
    if request.method == 'POST':
        form = TrabajoForm(request.POST)
        if form.is_valid():
            trabajo = form.save(commit=False)
            trabajo.trabajador = request.user
            trabajo.save()
            return redirect('historial')
    else:
        form = TrabajoForm(initial={'fecha': timezone.now().date()})
    return render(request, 'registros/crear_trabajo.html', {'form': form})


@login_required
def historial(request):
    trabajos = Trabajo.objects.all()
    f = TrabajoFilter(request.GET, queryset=trabajos)
    return render(request, 'registros/historial.html', {'filter': f})


@login_required
@user_passes_test(lambda u: u.groups.filter(name='Supervisor').exists() or u.is_superuser or u.groups.filter(name='Admin').exists())
def pendientes(request):
    trabajos = Trabajo.objects.filter(supervisor=request.user, aprobado=False)
    return render(request, 'registros/pendientes.html', {'trabajos': trabajos})


@login_required
def aprobar_trabajo(request, pk):
    trabajo = get_object_or_404(Trabajo, pk=pk)
    if request.user == trabajo.supervisor:
        trabajo.aprobado = True
        trabajo.save()
    return redirect('pendientes')


@login_required
def export_historial_xlsx(request):
    trabajos = Trabajo.objects.all()
    filter_trabajos = TrabajoFilter(request.GET, queryset=trabajos)
    trabajos = filter_trabajos.qs

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Historial_Trabajos.xlsx'

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'Historial de Trabajos'

    columns = [
        'Fecha', 'Faena', 'Máquina', 'Trabajo', 'Horómetro Inicial',
        'Horómetro Final', 'Total de Horas', 'Petróleo (litros)',
        'Aceite (tipo y litros)', 'Observaciones', 'Supervisor', 'Trabajador', 'Aprobado'
    ]
    row_num = 1

    for col_num, column_title in enumerate(columns, 1):
        column_letter = get_column_letter(col_num)
        worksheet[f'{column_letter}{row_num}'] = column_title

    for trabajo in trabajos:
        row_num += 1
        row = [
            trabajo.fecha,
            trabajo.faena.nombre,  # Convertir instancia a nombre
            trabajo.maquina.nombre,  # Convertir instancia a nombre
            trabajo.trabajo,
            trabajo.horometro_inicial,
            trabajo.horometro_final,
            trabajo.total_horas,
            trabajo.petroleo_litros,
            trabajo.aceite_tipo_litros,
            trabajo.observaciones,
            trabajo.supervisor.username if trabajo.supervisor else '',
            trabajo.trabajador.username if trabajo.trabajador else '',
            'Sí' if trabajo.aprobado else 'No'
        ]
        for col_num, cell_value in enumerate(row, 1):
            column_letter = get_column_letter(col_num)
            worksheet[f'{column_letter}{row_num}'] = cell_value

    workbook.save(response)
    return response


@login_required
def register_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'registros/register_user.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='Admin').exists())
def listar_usuarios(request):
    usuarios = User.objects.all()
    return render(request, 'registros/listar_usuarios.html', {'usuarios': usuarios})


@login_required
def crear_maquina(request):
    if request.method == 'POST':
        form = MaquinaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_maquinas')
    else:
        form = MaquinaForm()
    return render(request, 'registros/crear_maquina.html', {'form': form})


@login_required
def listar_maquinas(request):
    maquinas = Maquina.objects.all()
    # Crear un formulario para cada máquina
    forms = {maquina.pk: MaquinaForm(instance=maquina) for maquina in maquinas}

    if request.method == 'POST':
        maquina_id = request.POST.get('maquina_id')
        if maquina_id:
            maquina = get_object_or_404(Maquina, pk=maquina_id)
            form = MaquinaForm(request.POST, instance=maquina)
            if form.is_valid():
                form.save()
                # Redirigir para evitar reenviar el formulario
                return redirect('listar_maquinas')
            else:
                # Reemplazar con el formulario que tiene errores
                forms[int(maquina_id)] = form

    return render(request, 'registros/listar_maquinas.html', {'maquinas': maquinas, 'forms': forms})


@login_required
def eliminar_maquina(request, pk):
    maquina = get_object_or_404(Maquina, pk=pk)
    if request.method == 'POST':
        maquina.delete()
        return redirect('listar_maquinas')
    return render(request, 'registros/eliminar_maquina.html', {'maquina': maquina})


@login_required
def crear_faena(request):
    if request.method == 'POST':
        form = FaenaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_faenas')
    else:
        form = FaenaForm()
    return render(request, 'registros/crear_faena.html', {'form': form})


@login_required
def editar_faena(request, pk):
    faena = get_object_or_404(Faena, pk=pk)
    if request.method == 'POST':
        form = FaenaForm(request.POST, instance=faena)
        if form.is_valid():
            form.save()
            return redirect('listar_faenas')
    else:
        form = FaenaForm(instance=faena)
    return render(request, 'registros/editar_faena.html', {'form': form, 'faena': faena})


@login_required
def eliminar_faena(request, pk):
    faena = get_object_or_404(Faena, pk=pk)
    if request.method == 'POST':
        faena.delete()
        return redirect('listar_faenas')
    return render(request, 'registros/eliminar_faena.html', {'faena': faena})


@login_required
def listar_faenas(request):
    faenas = Faena.objects.all()
    # Crear un formulario para cada faena
    forms = {faena.pk: FaenaForm(instance=faena) for faena in faenas}

    if request.method == 'POST':
        faena_id = request.POST.get('faena_id')
        if faena_id:
            faena = get_object_or_404(Faena, pk=faena_id)
            form = FaenaForm(request.POST, instance=faena)
            if form.is_valid():
                form.save()
                # Redirigir para evitar reenviar el formulario
                return redirect('listar_faenas')
            else:
                # Reemplazar con el formulario que tiene errores
                forms[int(faena_id)] = form

    return render(request, 'registros/listar_faenas.html', {'faenas': faenas, 'forms': forms})


@login_required
def generar_pdf_trabajo(request, pk):
    trabajo = get_object_or_404(Trabajo, pk=pk)

    if request.method == 'POST' and request.FILES.get('logo'):
        logo = request.FILES['logo']
        logo_path = default_storage.save(
            f'logos/{logo.name}', ContentFile(logo.read()))

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=Trabajo_{trabajo.fecha}.pdf'

        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter

        # Añadir el logo con más margen desde la parte superior
        if logo_path:
            p.drawImage(os.path.join(settings.MEDIA_ROOT, logo_path), width -
                        2 * inch, height - inch, width=1 * inch, height=0.75 * inch)

        # Título con más espacio desde la parte superior
        p.setFont("Helvetica-Bold", 16)
        p.drawString(inch, height - 1.8 * inch, "Reporte de Trabajo")

        # Líneas de separación
        p.setStrokeColor(colors.grey)
        p.setLineWidth(0.5)
        p.line(inch, height - 1.85 * inch, width - inch, height - 1.85 * inch)

        # Datos del trabajo
        p.setFont("Helvetica", 12)
        y = height - 2.5 * inch
        left_column_x = inch + 10
        right_column_x = width / 2 + 10
        line_height = 16

        detalles = [
            ("Fecha", trabajo.fecha),
            ("Faena", trabajo.faena.nombre),
            ("Máquina", trabajo.maquina.nombre),
            ("Trabajo", trabajo.trabajo),
            ("Tipo de Medida", trabajo.tipo_medida),
            ("Horómetro Inicial", trabajo.horometro_inicial),
            ("Horómetro Final", trabajo.horometro_final),
            ("Total de Horas", trabajo.total_horas),
            ("Petróleo (litros)", trabajo.petroleo_litros),
            ("Aceite (tipo y litros)", trabajo.aceite_tipo_litros),
            ("Observaciones", trabajo.observaciones),
            ("Supervisor", trabajo.supervisor.username),
            ("Trabajador", trabajo.trabajador.username)
        ]

        for i, (label, value) in enumerate(detalles):
            if i % 2 == 0:
                p.drawString(left_column_x, y, f"{label}: {value}")
            else:
                p.drawString(right_column_x, y, f"{label}: {value}")
                y -= line_height
            if label == "Observaciones":
                y -= line_height  # Extra espacio después de observaciones

        p.showPage()
        p.save()

        return response
    else:
        return redirect('historial')


@login_required
def upload_logo(request):
    if request.method == 'POST':
        form = LogoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            logo = form.cleaned_data['logo']
            fs = FileSystemStorage()
            filename = fs.save(logo.name, logo)
            request.session['logo_path'] = fs.url(filename)
            return redirect('home')
    else:
        form = LogoUploadForm()
    return render(request, 'registros/upload_logo.html', {'form': form})
