from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def homepage(request):
    index = settings.FRONTEND_DIST / 'index.html'
    if not index.is_file():
        return HttpResponse('FRAME frontend has not been built. Run npm run build.', status=503, content_type='text/plain')
    response = FileResponse(index.open('rb'), content_type='text/html')
    response['Cache-Control'] = 'no-cache'
    return response
