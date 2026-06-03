from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from apiApp.models import MetodoPago
from .utils import staff_required, _extract_cloudinary_public_id


@login_required
@user_passes_test(staff_required)
def pago_list(request):
    metodos = MetodoPago.objects.all()
    return render(request, 'dashboard/pages/pagos.html', {
        'metodos': metodos,
    })


@login_required
@user_passes_test(staff_required)
def pago_create(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        numero_cuenta = request.POST.get('numero_cuenta', '')
        if not nombre:
            messages.error(request, 'El nombre es obligatorio.')
        elif MetodoPago.objects.filter(nombre=nombre).exists():
            messages.error(request, 'Ya existe un método de pago con ese nombre.')
        else:
            metodo = MetodoPago(
                nombre=nombre,
                descripcion=descripcion,
                numero_cuenta=numero_cuenta,
            )
            qr_file = request.FILES.get('qr_imagen')
            qr_url = request.POST.get('qr_imagen_url', '').strip()
            if qr_file:
                metodo.qr_imagen = qr_file
            elif qr_url:
                public_id = _extract_cloudinary_public_id(qr_url)
                if public_id:
                    metodo.qr_imagen = public_id
            metodo.save()
            messages.success(request, f'Método de pago "{nombre}" creado correctamente.')
            return redirect('pago_list')
    return render(request, 'dashboard/pages/pago_form.html', {'metodo': None})


@login_required
@user_passes_test(staff_required)
def pago_update(request, pk):
    metodo = get_object_or_404(MetodoPago, pk=pk)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        numero_cuenta = request.POST.get('numero_cuenta', '')
        if not nombre:
            messages.error(request, 'El nombre es obligatorio.')
        elif MetodoPago.objects.filter(nombre=nombre).exclude(pk=pk).exists():
            messages.error(request, 'Ya existe otro método de pago con ese nombre.')
        else:
            metodo.nombre = nombre
            metodo.descripcion = descripcion
            metodo.numero_cuenta = numero_cuenta

            qr_file = request.FILES.get('qr_imagen')
            qr_url = request.POST.get('qr_imagen_url', '').strip()
            eliminar_qr = request.POST.get('eliminar_qr')

            if eliminar_qr and metodo.qr_imagen:
                metodo.qr_imagen = None
            elif qr_file:
                metodo.qr_imagen = qr_file
            elif qr_url:
                public_id = _extract_cloudinary_public_id(qr_url)
                if public_id:
                    metodo.qr_imagen = public_id

            metodo.save()
            messages.success(request, f'Método de pago actualizado correctamente.')
            return redirect('pago_list')
    return render(request, 'dashboard/pages/pago_form.html', {'metodo': metodo})


@login_required
@user_passes_test(staff_required)
def pago_delete(request, pk):
    metodo = get_object_or_404(MetodoPago, pk=pk)
    if request.method == 'POST':
        nombre = metodo.nombre
        metodo.delete()
        messages.success(request, f'Método de pago "{nombre}" eliminado correctamente.')
    return redirect('pago_list')
