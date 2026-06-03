from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse

from .utils import staff_required


@login_required
@user_passes_test(staff_required)
def cloudinary_imagenes_api(request):
    import cloudinary.api
    try:
        tipo = request.GET.get('tipo', 'imagen')
        resource_type = 'video' if tipo == 'video' else 'image'
        next_cursor = request.GET.get('next_cursor')
        params = {'resource_type': resource_type, 'type': 'upload', 'max_results': 50}
        if next_cursor:
            params['next_cursor'] = next_cursor
        result = cloudinary.api.resources(**params)
        images = []
        for r in result.get('resources', []):
            entry = {
                'public_id': r['public_id'],
                'url': r['secure_url'],
                'format': r.get('format'),
                'width': r.get('width'),
                'height': r.get('height'),
            }
            if resource_type == 'video':
                import cloudinary.utils
                thumb_url, _ = cloudinary.utils.cloudinary_url(
                    r['public_id'],
                    resource_type='video',
                    width=300,
                    height=300,
                    crop='fill',
                    format='jpg'
                )
                entry['thumbnail_url'] = thumb_url
            images.append(entry)
        total_count = len(result.get('resources', []))
        has_more = result.get('next_cursor') is not None
        return JsonResponse({
            'images': images,
            'next_cursor': result.get('next_cursor'),
            'total_count': total_count,
            'has_more': has_more,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(staff_required)
def cloudinary_imagenes_delete(request):
    import cloudinary.uploader
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    public_id = request.POST.get('public_id', '').strip()
    tipo = request.POST.get('tipo', 'imagen')
    resource_type = 'video' if tipo == 'video' else 'image'
    if not public_id:
        return JsonResponse({'error': 'public_id requerido'}, status=400)
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
