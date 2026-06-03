from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count
from django.contrib import messages

from apiApp.models import Categoria
from .utils import staff_required


@login_required
@user_passes_test(staff_required)
def categoria_list(request):
    categorias = Categoria.objects.annotate(total_productos=Count('productos')).all()
    return render(request, 'dashboard/pages/categorias.html', {
        'categorias': categorias,
    })


@login_required
@user_passes_test(staff_required)
def categoria_create(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        if not nombre:
            messages.error(request, 'El nombre es obligatorio.')
        elif Categoria.objects.filter(nombre=nombre).exists():
            messages.error(request, 'Ya existe una categoría con ese nombre.')
        else:
            Categoria.objects.create(nombre=nombre)
            messages.success(request, f'Categoría "{nombre}" creada correctamente.')
            return redirect('categoria_list')
    return render(request, 'dashboard/pages/categoria_form.html', {'categoria': None})


@login_required
@user_passes_test(staff_required)
def categoria_update(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        if not nombre:
            messages.error(request, 'El nombre es obligatorio.')
        elif Categoria.objects.filter(nombre=nombre).exclude(pk=pk).exists():
            messages.error(request, 'Ya existe otra categoría con ese nombre.')
        else:
            categoria.nombre = nombre
            categoria.save()
            messages.success(request, f'Categoría actualizada correctamente.')
            return redirect('categoria_list')
    return render(request, 'dashboard/pages/categoria_form.html', {'categoria': categoria})


@login_required
@user_passes_test(staff_required)
def categoria_delete(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        nombre = categoria.nombre
        categoria.delete()
        messages.success(request, f'Categoría "{nombre}" eliminada correctamente.')
    return redirect('categoria_list')
