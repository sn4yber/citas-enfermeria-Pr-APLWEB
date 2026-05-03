from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging
import traceback

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is not None:
        response.data = {
            'success': False,
            'error': {
                'code': response.status_code,
                'message': str(exc.detail) if hasattr(exc, 'detail') else str(exc),
            }
        }
        response.headers['X-Content-Type-Options'] = 'nosniff'
    else:
        logger.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
        response = Response(
            {
                'success': False,
                'error': {
                    'code': 500,
                    'message': 'Error interno del servidor'
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return response


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if request.user.is_authenticated and request.method in ['POST', 'PUT', 'DELETE']:
            logger.info(f"User {request.user.id} {request.method} {request.path}")
        
        return response