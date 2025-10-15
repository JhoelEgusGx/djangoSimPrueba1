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

from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import hashlib



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
# 🤖 CHATBOT CON GEMINI - CORREGIDO
# ===============================

# Agregar esto al inicio del archivo después de los imports
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_client_ip(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def check_rate_limit(ip_address):
    """
    Verifica si el cliente ha excedido el límite de requests
    Retorna (puede_continuar, tiempo_espera)
    """
    cache_key = f"chatbot_rate_{ip_address}"
    requests = cache.get(cache_key, [])
    now = timezone.now()
    
    # Limpiar requests antiguos (últimos 60 segundos)
    requests = [req_time for req_time in requests if now - req_time < timedelta(seconds=60)]
    
    # Límite: 10 mensajes por minuto
    if len(requests) >= 10:
        oldest_request = min(requests)
        wait_time = 60 - (now - oldest_request).seconds
        return False, wait_time
    
    # Agregar nuevo request
    requests.append(now)
    cache.set(cache_key, requests, 60)
    
    return True, 0

def check_daily_limit(ip_address):
    """Verifica límite diario por IP"""
    cache_key = f"chatbot_daily_{ip_address}"
    count = cache.get(cache_key, 0)
    
    # ✅ CAMBIADO: Límite de 30 a 20 mensajes por día
    if count >= 20:
        return False
    
    cache.set(cache_key, count + 1, 86400)  # 24 horas
    return True

def get_cached_response(user_message):
    """Cachea respuestas comunes para ahorrar API calls"""
    message_hash = hashlib.md5(user_message.lower().strip().encode()).hexdigest()
    cache_key = f"chatbot_response_{message_hash}"
    
    cached = cache.get(cache_key)
    if cached:
        print(f"✅ Respuesta cacheada para: {user_message[:30]}...")
    return cached

def cache_response(user_message, response):
    """Guarda respuesta en cache por 1 hora"""
    message_hash = hashlib.md5(user_message.lower().strip().encode()).hexdigest()
    cache_key = f"chatbot_response_{message_hash}"
    cache.set(cache_key, response, 3600)  # 1 hora


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
    """Vista optimizada del chatbot con rate limiting y cache"""
    
    if request.method == "POST":
        try:
            # 🛡️ Obtener IP del cliente
            client_ip = get_client_ip(request)
            
            # 🛡️ Verificar rate limiting (por minuto)
            can_proceed, wait_time = check_rate_limit(client_ip)
            if not can_proceed:
                return JsonResponse({
                    "reply": f"⏱️ Por favor espera {wait_time} segundos antes de enviar otro mensaje.",
                    "rate_limited": True
                }, status=429)
            
            # 🛡️ Verificar límite diario
            if not check_daily_limit(client_ip):
                return JsonResponse({
                    "reply": "Has alcanzado el límite diario de mensajes. 😅 Vuelve mañana o contáctanos por WhatsApp al 940310504.",
                    "daily_limit_reached": True
                }, status=429)
            
            data = json.loads(request.body)
            user_message = data.get("message", "").strip()
            historial = data.get("history", [])
            
            if not user_message:
                return JsonResponse({"error": "Mensaje vacío"}, status=400)
            
            # Validar longitud del mensaje
            if len(user_message) > 500:
                return JsonResponse({
                    "reply": "Tu mensaje es demasiado largo. Por favor, hazlo más breve. 📝"
                }, status=400)
            
            # 💾 Verificar si hay respuesta cacheada
            cached_reply = get_cached_response(user_message)
            if cached_reply:
                return JsonResponse({"reply": cached_reply, "from_cache": True})
            
            # Obtener contexto actualizado de la tienda
            contexto_tienda = obtener_contexto_tienda()
            
            # ✅ AGREGADO: Construir historial con debug
            historial_texto = ""
            historial_filtrado = [msg for msg in historial if not msg.get("isWelcome", False)]
            
            # 🐛 DEBUG: Ver qué historial llega
            print(f"\n📊 === DEBUG CHATBOT ===")
            print(f"📊 Historial recibido: {len(historial)} mensajes")
            print(f"📊 Historial filtrado: {len(historial_filtrado)} mensajes")
            
            for msg in historial_filtrado[-6:]:  # Solo últimos 6 (3 intercambios)
                rol = msg.get("sender", "user")
                texto = msg.get("text", "")
                if rol == "user":
                    historial_texto += f"Usuario: {texto}\n"
                else:
                    historial_texto += f"Asistente: {texto}\n"
            
            if historial_texto:
                historial_texto = historial_texto.strip() + "\n"
                print(f"✅ Historial construido:\n{historial_texto}")
            else:
                print("⚠️ No hay historial previo - Primera interacción")
            
            print(f"💬 Mensaje actual: {user_message}")
            print(f"========================\n")
            
            # ✅ MEJORADO: Prompt con instrucciones más explícitas
            prompt = f"""
Eres un asistente virtual experto y amigable de **Gobady Perú**, una tienda online de productos importados.

{contexto_tienda}

=== INSTRUCCIONES CRÍTICAS ===
1. Responde de forma conversacional, amigable y profesional
2. **NUNCA repitas saludos como "Hola" si ya hay historial de conversación**
3. Continúa la conversación de forma natural según el contexto previo
4. Si preguntan por productos, menciona nombre, descripción, precio según cantidad y stock
5. Si preguntan por precios específicos, usa las tarifas exactas del contexto
6. Si no sabes algo, sugiere visitar la web o contactar por WhatsApp al 940310504
7. Usa emojis ocasionalmente (máximo 1 por mensaje)
8. Mantén respuestas CORTAS (máximo 2-3 líneas)
9. Ubicación: Av. Óscar R. Benavides 486, Lima - Perú (es almacén, no tienda física)

{f"=== CONVERSACIÓN PREVIA ===" if historial_texto else "=== INICIO DE CONVERSACIÓN ==="}
{historial_texto if historial_texto else "Primera interacción con el usuario."}

=== MENSAJE ACTUAL DEL USUARIO ===
{user_message}

=== TU RESPUESTA (sin repetir saludos si ya hay conversación) ==="""

            # Crear modelo con límites más estrictos
            model = genai.GenerativeModel(
                "gemini-2.0-flash-exp",
                generation_config={
                    "temperature": 0.6,  # Menos creativo = más predecible
                    "top_p": 0.9,
                    "top_k": 30,
                    "max_output_tokens": 200,  # Respuestas más cortas
                }
            )
            
            response = model.generate_content(prompt)
            
            if not response or not response.text:
                return JsonResponse({
                    "reply": "Disculpa, tuve un problema. ¿Podrías reformular tu pregunta? 😊"
                })
            
            reply = response.text.strip()
            
            # Limitar longitud de respuesta
            if len(reply) > 500:
                reply = reply[:500] + "..."
            
            print(f"🤖 Respuesta generada: {reply[:100]}...")
            
            # 💾 Cachear la respuesta
            cache_response(user_message, reply)
            
            return JsonResponse({"reply": reply, "from_cache": False})
            
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)
        except Exception as e:
            print(f"❌ Error en chatbot: {str(e)}")
            return JsonResponse({
                "reply": "Lo siento, ocurrió un error. Intenta de nuevo en unos momentos. 🙏"
            }, status=500)
    
    return JsonResponse({"error": "Método no permitido"}, status=405)