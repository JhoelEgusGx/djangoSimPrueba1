import re
from decimal import Decimal

from apiApp.models import Tarifa, ImagenProducto, VideoProducto
from django.contrib import messages


def staff_required(user):
    return user.is_staff


def _extract_cloudinary_public_id(url_or_id):
    if not url_or_id:
        return None
    if not url_or_id.startswith('http'):
        return url_or_id.rsplit('.', 1)[0] if '.' in url_or_id.replace('/', '') else url_or_id
    m = re.search(r'/upload/(?:[^/]+/)*(?:v\d+/)?(.+)', url_or_id)
    if m:
        pid = m.group(1)
        pid = pid.rsplit('.', 1)[0] if '.' in pid else pid
        return pid
    return url_or_id


def _guardar_tarifas(request, producto):
    minimos = request.POST.getlist('tarifa_minimo')
    maximos = request.POST.getlist('tarifa_maximo')
    precios = request.POST.getlist('tarifa_precio')
    max_count = max(len(minimos), len(maximos), len(precios))
    for i in range(max_count):
        minimo = minimos[i].strip() if i < len(minimos) else ''
        precio = precios[i].strip() if i < len(precios) else ''
        maximo = maximos[i].strip() if i < len(maximos) else ''
        if not minimo or not precio:
            continue
        try:
            maximo_val = int(maximo) if maximo else None
            Tarifa.objects.create(
                producto=producto,
                minimo=int(minimo),
                maximo=maximo_val,
                precio_unitario=Decimal(precio),
            )
        except Exception:
            continue


def _guardar_imagenes_y_videos(request, producto):
    eliminar_img = request.POST.getlist('eliminar_imagen')
    if eliminar_img:
        ImagenProducto.objects.filter(id__in=eliminar_img, producto=producto).delete()
    eliminar_vid = request.POST.getlist('eliminar_video')
    if eliminar_vid:
        VideoProducto.objects.filter(id__in=eliminar_vid, producto=producto).delete()

    for img_file in request.FILES.getlist('imagenes'):
        try:
            ImagenProducto.objects.create(producto=producto, imagen=img_file)
        except Exception:
            messages.warning(request, f'No se pudo subir la imagen "{img_file.name}". Verifica Cloudinary.')

    for vid_file in request.FILES.getlist('videos'):
        try:
            VideoProducto.objects.create(producto=producto, video=vid_file)
        except Exception:
            messages.warning(request, f'No se pudo subir el video "{vid_file.name}". Verifica Cloudinary.')

    for url in request.POST.getlist('imagen_url'):
        url = url.strip()
        if not url:
            continue
        public_id = _extract_cloudinary_public_id(url)
        if public_id:
            try:
                ImagenProducto.objects.create(producto=producto, imagen=public_id)
            except Exception as e:
                messages.warning(request, f'No se pudo usar la imagen desde Cloudinary: {e}')
        else:
            messages.warning(request, f'URL de Cloudinary no válida: {url}')

    video_url = request.POST.get('video_url', '').strip()
    if video_url:
        public_id = _extract_cloudinary_public_id(video_url)
        if public_id:
            try:
                VideoProducto.objects.create(producto=producto, video=public_id)
            except Exception as e:
                messages.warning(request, f'No se pudo usar el video desde Cloudinary: {e}')
        else:
            messages.warning(request, f'URL de Cloudinary no válida: {video_url}')
