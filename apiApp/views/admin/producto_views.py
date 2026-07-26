from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages

from apiApp.models import Producto, Categoria, Proveedor
from .utils import staff_required, _guardar_tarifas, _guardar_imagenes_y_videos


@login_required
@user_passes_test(staff_required)
def producto_list_api(request):
    q = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '').strip()
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()

    productos = Producto.objects.prefetch_related('categorias', 'imagenes', 'tarifas', 'proveedores').filter(activo=True).order_by('-fecha_ingreso')

    if q:
        productos = productos.filter(nombre__icontains=q)
    if categoria_id:
        productos = productos.filter(categorias__id=categoria_id)
    date_conditions = []
    date_params = []
    if fecha_desde:
        date_conditions.append('DATE(fecha_ingreso) >= %s')
        date_params.append(fecha_desde)
    if fecha_hasta:
        date_conditions.append('DATE(fecha_ingreso) <= %s')
        date_params.append(fecha_hasta)
    if date_conditions:
        productos = productos.extra(where=[' AND '.join(date_conditions)], params=date_params)

    data = []
    for p in productos:
        primera_imagen = p.imagenes.first()
        primera_tarifa = p.tarifas.first()
        data.append({
            'id': p.id,
            'nombre': p.nombre,
            'descripcion': p.descripcion[:80],
            'cantidad': p.cantidad,
            'mostrar_en_pagina': p.mostrar_en_pagina,
            'fecha_ingreso': p.fecha_ingreso.strftime('%d/%m/%Y'),
            'fecha_ingreso_iso': p.fecha_ingreso.isoformat(),
            'categorias': [{'id': c.id, 'nombre': c.nombre} for c in p.categorias.all()],
            'imagen_url': primera_imagen.imagen.url if primera_imagen and primera_imagen.imagen else None,
            'precio': str(primera_tarifa.precio_unitario) if primera_tarifa else None,
            'proveedores': [{'id': pr.id, 'nombre': pr.nombre} for pr in p.proveedores.all()],
        })

    return JsonResponse({'data': data})


@login_required
@user_passes_test(staff_required)
def producto_list(request):
    query = request.GET.get('q', '')
    categorias = Categoria.objects.all()
    proveedores = Proveedor.objects.all().order_by('nombre')
    productos = Producto.objects.prefetch_related('categorias', 'tarifas', 'imagenes', 'proveedores').filter(activo=True).order_by('-fecha_ingreso')
    if query:
        productos = productos.filter(nombre__icontains=query)
    return render(request, 'dashboard/pages/productos.html', {
        'productos': productos,
        'query': query,
        'categorias': categorias,
        'proveedores': proveedores,
    })


@login_required
@user_passes_test(staff_required)
def producto_create(request):
    categorias = Categoria.objects.all()
    proveedores = Proveedor.objects.all().order_by('nombre')
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        cantidad = request.POST.get('cantidad', 300)
        mostrar_en_pagina = request.POST.get('mostrar_en_pagina') == '1'
        categorias_ids = request.POST.getlist('categorias')
        proveedores_ids = request.POST.getlist('proveedores')

        if not nombre:
            messages.error(request, 'El nombre es obligatorio.')
        else:
            producto = Producto.objects.create(
                nombre=nombre,
                descripcion=descripcion or '',
                cantidad=int(cantidad) if cantidad else 300,
                mostrar_en_pagina=mostrar_en_pagina,
            )
            if categorias_ids:
                producto.categorias.set(Categoria.objects.filter(id__in=categorias_ids))
            if proveedores_ids:
                producto.proveedores.set(Proveedor.objects.filter(id__in=proveedores_ids))

            _guardar_tarifas(request, producto)
            _guardar_imagenes_y_videos(request, producto)

            if not producto.imagenes.exists():
                producto.delete()
                messages.error(request, 'Debes agregar al menos una imagen (subir archivo o pegar URL de Cloudinary).')
                return redirect('producto_create')

            messages.success(request, f'Producto "{nombre}" creado correctamente.')
            return redirect('producto_list')

    return render(request, 'dashboard/pages/producto_form.html', {
        'categorias': categorias,
        'proveedores': proveedores,
        'producto': None,
        'tarifas': [],
    })


@login_required
@user_passes_test(staff_required)
def producto_update(request, pk):
    producto = get_object_or_404(
        Producto.objects.prefetch_related('categorias', 'tarifas', 'imagenes', 'videos', 'proveedores'),
        pk=pk
    )
    categorias = Categoria.objects.all()
    proveedores = Proveedor.objects.all().order_by('nombre')
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        cantidad = request.POST.get('cantidad', 300)
        mostrar_en_pagina = request.POST.get('mostrar_en_pagina') == '1'
        categorias_ids = request.POST.getlist('categorias')
        proveedores_ids = request.POST.getlist('proveedores')

        if not nombre:
            messages.error(request, 'El nombre es obligatorio.')
        else:
            producto.nombre = nombre
            producto.descripcion = descripcion or ''
            producto.cantidad = int(cantidad) if cantidad else 300
            producto.mostrar_en_pagina = mostrar_en_pagina
            producto.save()
            producto.categorias.set(Categoria.objects.filter(id__in=categorias_ids))
            producto.proveedores.set(Proveedor.objects.filter(id__in=proveedores_ids))

            producto.tarifas.all().delete()
            _guardar_tarifas(request, producto)
            _guardar_imagenes_y_videos(request, producto)

            messages.success(request, f'Producto "{nombre}" actualizado correctamente.')
            return redirect('producto_list')

    return render(request, 'dashboard/pages/producto_form.html', {
        'categorias': categorias,
        'proveedores': proveedores,
        'producto': producto,
        'tarifas': producto.tarifas.all(),
    })


@login_required
@user_passes_test(staff_required)
def producto_delete(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        nombre = producto.nombre
        producto.activo = False
        producto.save()
        messages.success(request, f'Producto "{nombre}" archivado correctamente.')
        return redirect('producto_list')
    return render(request, 'dashboard/pages/productos.html', {
        'error': 'Método no permitido.'
    })


@login_required
@user_passes_test(staff_required)
def papelera_list(request):
    productos = Producto.objects.prefetch_related('categorias', 'tarifas', 'imagenes', 'proveedores').filter(activo=False).order_by('-fecha_ingreso')
    return render(request, 'dashboard/pages/papelera.html', {
        'productos': productos,
    })


@login_required
@user_passes_test(staff_required)
def papelera_restore(request, pk):
    producto = get_object_or_404(Producto, pk=pk, activo=False)
    if request.method == 'POST':
        producto.activo = True
        producto.save()
        messages.success(request, f'Producto "{producto.nombre}" restaurado correctamente.')
    return redirect('papelera_list')


@login_required
@user_passes_test(staff_required)
def papelera_delete_permanente(request, pk):
    producto = get_object_or_404(Producto, pk=pk, activo=False)
    if request.method == 'POST':
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f'Producto "{nombre}" eliminado permanentemente.')
    return redirect('papelera_list')
