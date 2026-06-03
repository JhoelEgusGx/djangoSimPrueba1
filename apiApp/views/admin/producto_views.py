from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages

from apiApp.models import Producto, Categoria
from .utils import staff_required, _guardar_tarifas, _guardar_imagenes_y_videos


@login_required
@user_passes_test(staff_required)
def producto_list_api(request):
    q = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '').strip()
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()

    productos = Producto.objects.prefetch_related('categorias', 'imagenes').all().order_by('-fecha_ingreso')

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
        data.append({
            'id': p.id,
            'nombre': p.nombre,
            'descripcion': p.descripcion[:80],
            'cantidad': p.cantidad,
            'fecha_ingreso': p.fecha_ingreso.strftime('%d/%m/%Y'),
            'fecha_ingreso_iso': p.fecha_ingreso.isoformat(),
            'categorias': [{'id': c.id, 'nombre': c.nombre} for c in p.categorias.all()],
            'imagen_url': primera_imagen.imagen.url if primera_imagen and primera_imagen.imagen else None,
        })

    return JsonResponse({'data': data})


@login_required
@user_passes_test(staff_required)
def producto_list(request):
    query = request.GET.get('q', '')
    categorias = Categoria.objects.all()
    productos = Producto.objects.prefetch_related('categorias', 'tarifas', 'imagenes').all().order_by('-fecha_ingreso')
    if query:
        productos = productos.filter(nombre__icontains=query)
    return render(request, 'dashboard/pages/productos.html', {
        'productos': productos,
        'query': query,
        'categorias': categorias,
    })


@login_required
@user_passes_test(staff_required)
def producto_create(request):
    categorias = Categoria.objects.all()
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        cantidad = request.POST.get('cantidad', 0)
        categorias_ids = request.POST.getlist('categorias')

        if not nombre:
            messages.error(request, 'El nombre es obligatorio.')
        else:
            producto = Producto.objects.create(
                nombre=nombre,
                descripcion=descripcion or '',
                cantidad=int(cantidad) if cantidad else 0,
            )
            if categorias_ids:
                producto.categorias.set(Categoria.objects.filter(id__in=categorias_ids))

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
        'producto': None,
        'tarifas': [],
    })


@login_required
@user_passes_test(staff_required)
def producto_update(request, pk):
    producto = get_object_or_404(
        Producto.objects.prefetch_related('categorias', 'tarifas', 'imagenes', 'videos'),
        pk=pk
    )
    categorias = Categoria.objects.all()
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        cantidad = request.POST.get('cantidad', 0)
        categorias_ids = request.POST.getlist('categorias')

        if not nombre:
            messages.error(request, 'El nombre es obligatorio.')
        else:
            producto.nombre = nombre
            producto.descripcion = descripcion or ''
            producto.cantidad = int(cantidad) if cantidad else 0
            producto.save()
            producto.categorias.set(Categoria.objects.filter(id__in=categorias_ids))

            producto.tarifas.all().delete()
            _guardar_tarifas(request, producto)
            _guardar_imagenes_y_videos(request, producto)

            messages.success(request, f'Producto "{nombre}" actualizado correctamente.')
            return redirect('producto_list')

    return render(request, 'dashboard/pages/producto_form.html', {
        'categorias': categorias,
        'producto': producto,
        'tarifas': producto.tarifas.all(),
    })


@login_required
@user_passes_test(staff_required)
def producto_delete(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f'Producto "{nombre}" eliminado correctamente.')
        return redirect('producto_list')
    return render(request, 'dashboard/pages/productos.html', {
        'error': 'Método no permitido.'
    })
