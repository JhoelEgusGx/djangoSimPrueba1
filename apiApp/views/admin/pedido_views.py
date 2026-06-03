from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages

from apiApp.models import Pedido, MetodoPago
from .utils import staff_required


@login_required
@user_passes_test(staff_required)
def pedido_list_api(request):
    q = request.GET.get('q', '').strip()
    metodo_pago_id = request.GET.get('metodo_pago', '').strip()
    envio = request.GET.get('envio', '').strip()
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()

    pedidos = Pedido.objects.select_related('metodo_pago').prefetch_related('items__producto').order_by('-fecha')

    if q:
        from django.db.models import Q
        pedidos = pedidos.filter(
            Q(codigo__icontains=q) | Q(nombre__icontains=q) |
            Q(apellido__icontains=q) | Q(dni__icontains=q) |
            Q(correo__icontains=q) | Q(telefono__icontains=q)
        )
    if metodo_pago_id:
        pedidos = pedidos.filter(metodo_pago__id=metodo_pago_id)
    if envio == 'lima':
        pedidos = pedidos.filter(envio_provincia=False)
    elif envio == 'provincia':
        pedidos = pedidos.filter(envio_provincia=True)

    date_conditions = []
    date_params = []
    if fecha_desde:
        date_conditions.append('DATE(fecha) >= %s')
        date_params.append(fecha_desde)
    if fecha_hasta:
        date_conditions.append('DATE(fecha) <= %s')
        date_params.append(fecha_hasta)
    if date_conditions:
        pedidos = pedidos.extra(where=[' AND '.join(date_conditions)], params=date_params)

    data = []
    for p in pedidos:
        data.append({
            'id': p.id,
            'codigo': p.codigo,
            'nombre': p.nombre,
            'apellido': p.apellido,
            'dni': p.dni,
            'correo': p.correo,
            'telefono': p.telefono,
            'envio_provincia': p.envio_provincia,
            'total': str(p.total),
            'fecha': p.fecha.strftime('%d/%m/%Y %H:%M'),
            'metodo_pago': p.metodo_pago.nombre if p.metodo_pago else '—',
        })

    return JsonResponse({'data': data})


@login_required
@user_passes_test(staff_required)
def pedido_list(request):
    pedidos = Pedido.objects.select_related('metodo_pago').prefetch_related('items__producto').order_by('-fecha')
    metodo_pagos = MetodoPago.objects.all()
    return render(request, 'dashboard/pages/pedidos.html', {
        'pedidos': pedidos,
        'metodo_pagos': metodo_pagos,
    })


@login_required
@user_passes_test(staff_required)
def pedido_detail(request, pk):
    pedido = get_object_or_404(
        Pedido.objects.select_related('metodo_pago').prefetch_related('items__producto'),
        pk=pk
    )
    return render(request, 'dashboard/pages/pedido_detail.html', {
        'pedido': pedido,
    })


@login_required
@user_passes_test(staff_required)
def pedido_delete(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if request.method == 'POST':
        codigo = pedido.codigo
        pedido.delete()
        messages.success(request, f'Pedido {codigo} eliminado correctamente.')
    return redirect('pedido_list')
