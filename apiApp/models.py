# Create your models here.
from django.db import models
from django.utils.html import escape
import random
import string

# ---------------------------✅
class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

# ---------------------------✅
class Producto(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    fecha_ingreso = models.DateField(auto_now_add=True)
    cantidad = models.PositiveIntegerField()
    categorias = models.ManyToManyField(Categoria, related_name='productos')

    def __str__(self):
        return self.nombre

# ---------------------------   
class Tarifa(models.Model):
    producto = models.ForeignKey(Producto, related_name='tarifas', on_delete=models.CASCADE)
    minimo = models.PositiveIntegerField()
    maximo = models.PositiveIntegerField(null=True, blank=True)  # null = sin límite
    precio_unitario = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        ordering = ['minimo']

    def __str__(self):
        return f"{self.producto.nombre} - {self.minimo}-{self.maximo or '∞'} unidades → S/{self.precio_unitario}"

# ---------------------------
class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, related_name='imagenes', on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='productos/imagenes/')

# ---------------------------
class VideoProducto(models.Model):
    producto = models.ForeignKey(Producto, related_name='videos', on_delete=models.CASCADE)
    video = models.FileField(upload_to='productos/videos/')

# ---------------------------
class MetodoPago(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    qr_imagen = models.ImageField(upload_to='pagos/qr/', blank=True, null=True)
    numero_cuenta = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return self.nombre

# ---------------------------
class Pedido(models.Model):
    codigo = models.CharField(max_length=5, unique=True, editable=False)
    fecha = models.DateTimeField(auto_now_add=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=8)
    telefono = models.CharField(max_length=9)
    correo = models.EmailField()
    envio_provincia = models.BooleanField(default=False)

    departamento = models.CharField(max_length=100, blank=True, null=True)
    provincia = models.CharField(max_length=100, blank=True, null=True)
    distrito = models.CharField(max_length=100, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True) 

    total = models.DecimalField(max_digits=10, decimal_places=2)

    metodo_pago = models.ForeignKey(MetodoPago, on_delete=models.PROTECT)

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self.generar_codigo_unico()
        super().save(*args, **kwargs)

    def generar_codigo_unico(self):
        while True:
            codigo = ''.join(random.choices(string.digits, k=5))
            if not Pedido.objects.filter(codigo=codigo).exists():
                return codigo

    def __str__(self):
        return f"Pedido {self.codigo}"

# ---------------------------
class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=8, decimal_places=2)

    def subtotal(self):
        return self.cantidad * self.precio_unitario
