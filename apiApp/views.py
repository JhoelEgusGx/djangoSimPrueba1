from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from utils.email_service import enviar_correo_pedido
from django.shortcuts import get_object_or_404

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import google.generativeai as genai
import json
import os

from .models import (
    Producto, Categoria, Tarifa,
    ImagenProducto, VideoProducto,
    MetodoPago, Pedido, PedidoItem
)
from .serializers import (
    ProductoSerializer, CategoriaSerializer, TarifaSerializer,
    ImagenProductoSerializer, VideoProductoSerializer,
    MetodoPagoSerializer, PedidoSerializer, PedidoItemSerializer
)

# ViewSets


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre', 'categorias__nombre']


class TarifaViewSet(viewsets.ModelViewSet):
    queryset = Tarifa.objects.all()
    serializer_class = TarifaSerializer


class ImagenProductoViewSet(viewsets.ModelViewSet):
    queryset = ImagenProducto.objects.all()
    serializer_class = ImagenProductoSerializer


class VideoProductoViewSet(viewsets.ModelViewSet):
    queryset = VideoProducto.objects.all()
    serializer_class = VideoProductoSerializer


class MetodoPagoViewSet(viewsets.ModelViewSet):
    queryset = MetodoPago.objects.all()
    serializer_class = MetodoPagoSerializer


class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all().order_by('-fecha')
    serializer_class = PedidoSerializer

    @action(detail=False, methods=['get'], url_path='codigo/(?P<codigo>[^/.]+)')
    def buscar_por_codigo(self, request, codigo=None):
        try:
            pedido = Pedido.objects.get(codigo=codigo)
            serializer = self.get_serializer(pedido)
            return Response(serializer.data)
        except Pedido.DoesNotExist:
            return Response({"error": "Pedido no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    # 📨 Sobrescribimos create para enviar correo al guardar pedido

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pedido = serializer.save()

        items_html = ""
        total_general = 0

        for item in request.data.get("items", []):
            producto = get_object_or_404(Producto, id=item["producto_id"])
            cantidad = int(item["cantidad"])

            # ✅ Buscar tarifa según cantidad
            tarifa = None
            for t in producto.tarifas.all():
                if (t.minimo is None or cantidad >= t.minimo) and (t.maximo is None or cantidad <= t.maximo):
                    tarifa = t
                    break

            if not tarifa:
                return Response(
                    {"error": f"No hay tarifa válida para {producto.nombre} con cantidad {cantidad}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            precio_unitario = float(tarifa.precio_unitario)
            subtotal = precio_unitario * cantidad
            total_general += subtotal

            # ✅ primera imagen (si existe)
            primera_imagen = producto.imagenes.first()
            imagen_url = primera_imagen.imagen.url if (
                primera_imagen and primera_imagen.imagen) else "https://via.placeholder.com/50"

            items_html += f"""
            <tr>
                <td style="padding:8px; border:1px solid #ddd; display:flex; align-items:center; gap:8px;">
                    <img src="{imagen_url}" alt="{producto.nombre}" width="50" height="50" style="object-fit:cover; border-radius:4px;">
                    <span>{producto.nombre}</span>
                </td>
                <td style="padding:8px; border:1px solid #ddd; text-align:center;">{cantidad}</td>
                <td style="padding:8px; border:1px solid #ddd; text-align:right;">S/. {precio_unitario:.2f}</td>
                <td style="padding:8px; border:1px solid #ddd; text-align:right;">S/. {subtotal:.2f}</td>
            </tr>
            """

        # 🚚 Envío a provincia
        envio = 0
        if pedido.envio_provincia:
            envio = 8
            total_general += envio

        # 📩 HTML del correo
        mensaje_html = f"""
        <div style="font-family: Arial, sans-serif; max-width:600px; margin:auto; border:1px solid #eee; padding:20px; border-radius:8px;">
            <h2 style="color:#0f172a; text-align:center;">¡Gracias por tu pedido, {pedido.nombre}!</h2>
            <p style="text-align:center;">Tu código de pedido es: <b>{pedido.codigo}</b></p>

            <h3 style="margin-top:30px;">Resumen de pedido</h3>
            <table style="width:100%; border-collapse:collapse; margin-top:10px;">
                <thead>
                    <tr style="background:#f1f5f9;">
                        <th style="padding:8px; border:1px solid #ddd;">Producto</th>
                        <th style="padding:8px; border:1px solid #ddd;">Cantidad</th>
                        <th style="padding:8px; border:1px solid #ddd;">Precio Unit.</th>
                        <th style="padding:8px; border:1px solid #ddd;">Subtotal</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>

            <div style="margin-top:20px; text-align:right;">
                {"<p>Envío a provincia: <b>S/. 8.00</b></p>" if envio else ""}
                <h3>Total: S/. {total_general:.2f}</h3>
            </div>

            <p style="margin-top:30px; text-align:center; color:#555;">
                Recibimos tu pedido y lo estamos preparando para enviarlo a tu domicilio.<br>
                ¡Gracias por confiar en <b>Gobady Perú</b>!
            </p>
        </div>
        """

        # enviar correo al cliente
        enviar_correo_pedido(
            cliente_email=pedido.correo,
            asunto="Confirmación de tu pedido en Gobady Perú",
            mensaje_html=mensaje_html
        )

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class PedidoItemViewSet(viewsets.ModelViewSet):
    queryset = PedidoItem.objects.all()
    serializer_class = PedidoItemSerializer

# Home page view if you want


def HomePage(request):
    return render(request, 'index.html')


# ===============================
# CONFIGURAR GEMINI
# ===============================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def obtener_contexto_tienda():
    """Genera información actualizada de productos, categorías y precios"""
    
    categorias = Categoria.objects.all()
    productos = Producto.objects.prefetch_related('categorias', 'tarifas').all()
    metodos_pago = MetodoPago.objects.all()
    
    contexto = "=== INFORMACIÓN DE GOBADY PERÚ ===\n\n"
    
    # Categorías disponibles
    contexto += "📦 CATEGORÍAS:\n"
    for cat in categorias:
        cantidad_productos = cat.productos.count()
        contexto += f"- {cat.nombre} ({cantidad_productos} productos)\n"
    
    contexto += "\n🛍️ PRODUCTOS DISPONIBLES:\n"
    for prod in productos:
        contexto += f"\n▪ {prod.nombre}\n"
        contexto += f"  Descripción: {prod.descripcion}\n"
        contexto += f"  Stock: {prod.cantidad} unidades\n"
        contexto += f"  Categorías: {', '.join([c.nombre for c in prod.categorias.all()])}\n"
        
        # Agregar tarifas
        if prod.tarifas.exists():
            contexto += "  Precios según cantidad:\n"
            for tarifa in prod.tarifas.all():
                rango = f"{tarifa.minimo}-{tarifa.maximo if tarifa.maximo else '∞'}"
                contexto += f"    • {rango} unidades → S/. {tarifa.precio_unitario} c/u\n"
    
    # Métodos de pago
    contexto += "\n💳 MÉTODOS DE PAGO:\n"
    for mp in metodos_pago:
        contexto += f"- {mp.nombre}: {mp.descripcion or 'Disponible'}\n"
    
    contexto += "\n📍 INFORMACIÓN DE ENVÍOS:\n"
    contexto += "- Envío a Lima: Consultar disponibilidad\n"
    contexto += "- Envío a provincia: S/. 8.00 adicionales\n"
    
    return contexto


@csrf_exempt
def chatbot(request):
    """Vista mejorada del chatbot con contexto completo y historial"""
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "").strip()
            historial = data.get("history", [])  # Recibe historial del frontend
            
            if not user_message:
                return JsonResponse({"error": "Mensaje vacío"}, status=400)
            
            # Obtener contexto actualizado de la tienda
            contexto_tienda = obtener_contexto_tienda()
            
            # Construir historial formateado
            historial_texto = ""
            for msg in historial[-6:]:  # Solo últimos 6 mensajes para no saturar
                rol = msg.get("sender", "user")
                texto = msg.get("text", "")
                if rol == "user":
                    historial_texto += f"Usuario: {texto}\n"
                else:
                    historial_texto += f"Asistente: {texto}\n"
            
            # Prompt mejorado con instrucciones claras
            prompt = f"""
Eres un asistente virtual experto y amigable de **Gobady Perú**, una tienda online de productos.

{contexto_tienda}

=== INSTRUCCIONES ===
1. Responde de forma conversacional, amigable y profesional
2. Si preguntan por productos, menciona nombre, descripción, precio según cantidad y stock
3. Si preguntan por precios específicos, usa las tarifas exactas del contexto
4. Si no sabes algo, sugiere visitar la web o contactar por WhatsApp
5. Usa emojis ocasionalmente para hacer la conversación más cálida
6. Si preguntan cómo comprar, explica que pueden hacerlo desde la web
7. Mantén respuestas concisas (máximo 3-4 líneas)

=== HISTORIAL DE CONVERSACIÓN ===
{historial_texto}

=== CONSULTA ACTUAL ===
Usuario: {user_message}

Asistente:"""

            # Crear modelo y generar respuesta
            model = genai.GenerativeModel(
                "gemini-2.0-flash-exp",
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 500,
                }
            )
            
            response = model.generate_content(prompt)
            
            if not response or not response.text:
                return JsonResponse({
                    "reply": "Disculpa, tuve un problema al procesar tu consulta. ¿Podrías reformularla? 😊"
                })
            
            reply = response.text.strip()
            
            # Agregar sugerencias si la respuesta es muy corta
            if len(reply) < 50:
                reply += "\n\n¿Hay algo más en lo que pueda ayudarte? 😊"
            
            return JsonResponse({"reply": reply})
            
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)
        except Exception as e:
            print(f"Error en chatbot: {str(e)}")
            return JsonResponse({
                "reply": "Lo siento, ocurrió un error inesperado. Por favor, intenta de nuevo en unos momentos. 🙏",
                "error": str(e)
            }, status=500)
    
    return JsonResponse({"error": "Método no permitido"}, status=405)