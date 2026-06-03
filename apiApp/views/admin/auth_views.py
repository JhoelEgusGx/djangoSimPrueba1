from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect

from apiApp.models import Producto, Pedido, Categoria, MetodoPago
from .utils import staff_required


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect('dashboard_home')
    else:
        form = AuthenticationForm()
    return render(request, 'dashboard/auth/login.html', {'form': form})


@login_required
@user_passes_test(staff_required)
def dashboard_home(request):
    total_productos = Producto.objects.count()
    total_pedidos = Pedido.objects.count()
    total_categorias = Categoria.objects.count()
    total_metodos_pago = MetodoPago.objects.count()

    pedidos_recientes = Pedido.objects.select_related('metodo_pago').order_by('-fecha')[:5]
    productos_bajo_stock = Producto.objects.filter(cantidad__lte=5).order_by('cantidad')[:10]

    return render(request, 'dashboard/pages/dashboard.html', {
        'total_productos': total_productos,
        'total_pedidos': total_pedidos,
        'total_categorias': total_categorias,
        'total_metodos_pago': total_metodos_pago,
        'pedidos_recientes': pedidos_recientes,
        'productos_bajo_stock': productos_bajo_stock,
    })
