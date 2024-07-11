from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Trabajo
from .forms import TrabajoForm, UserRegistrationForm
from .filters import TrabajoFilter
from django.utils import timezone
from django.http import HttpResponse
import openpyxl
from openpyxl.utils import get_column_letter
from django.contrib.auth.models import User


def home(request):
    return render(request, 'registros/home.html')


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
def aprobar_trabajo(request, pk):
    trabajo = get_object_or_404(Trabajo, pk=pk)
    if request.user == trabajo.supervisor:
        trabajo.aprobado = True
        trabajo.save()
    return redirect('pendientes')


@login_required
def pendientes(request):
    trabajos = Trabajo.objects.filter(supervisor=request.user, aprobado=False)
    return render(request, 'registros/pendientes.html', {'trabajos': trabajos})


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
            trabajo.faena,
            trabajo.maquina,
            trabajo.trabajo,
            trabajo.horometro_inicial,
            trabajo.horometro_final,
            trabajo.total_horas,
            getattr(trabajo, 'petroleo', ''),
            getattr(trabajo, 'aceite', ''),
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
def listar_usuarios(request):
    if request.user.is_superuser:  # Solo los superusuarios pueden ver esta lista
        usuarios = User.objects.all()
        return render(request, 'registros/listar_usuarios.html', {'usuarios': usuarios})
    else:
        return redirect('home')
