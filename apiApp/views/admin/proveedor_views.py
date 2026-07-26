from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from apiApp.models import Proveedor
from .utils import staff_required


@login_required
@user_passes_test(staff_required)
def proveedor_list(request):
    proveedores = Proveedor.objects.all().order_by('nombre')
    return render(request, 'dashboard/pages/proveedores.html', {
        'proveedores': proveedores,
    })


@login_required
@user_passes_test(staff_required)
def proveedor_create(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        ubicacion = request.POST.get('ubicacion', '').strip()
        if not nombre:
            messages.error(request, 'El nombre es obligatorio.')
        else:
            Proveedor.objects.create(nombre=nombre, ubicacion=ubicacion or None)
            messages.success(request, f'Proveedor "{nombre}" creado correctamente.')
            return redirect('proveedor_list')
    return render(request, 'dashboard/pages/proveedor_form.html', {
        'proveedor': None,
    })


@login_required
@user_passes_test(staff_required)
def proveedor_update(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        ubicacion = request.POST.get('ubicacion', '').strip()
        if not nombre:
            messages.error(request, 'El nombre es obligatorio.')
        else:
            proveedor.nombre = nombre
            proveedor.ubicacion = ubicacion or None
            proveedor.save()
            messages.success(request, f'Proveedor "{nombre}" actualizado correctamente.')
            return redirect('proveedor_list')
    return render(request, 'dashboard/pages/proveedor_form.html', {
        'proveedor': proveedor,
    })


@login_required
@user_passes_test(staff_required)
def proveedor_delete(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        nombre = proveedor.nombre
        proveedor.delete()
        messages.success(request, f'Proveedor "{nombre}" eliminado correctamente.')
        return redirect('proveedor_list')
    return redirect('proveedor_list')
