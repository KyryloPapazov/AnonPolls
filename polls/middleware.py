from django.utils.deprecation import MiddlewareMixin
from .utils import generate_unique_identifier


class UniqueIdentifierMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.COOKIES.get('unique_identifier'):
            unique_identifier = generate_unique_identifier()
            request.unique_identifier = unique_identifier
        else:
            request.unique_identifier = request.COOKIES.get('unique_identifier')

    def process_response(self, request, response):
        if not request.COOKIES.get('unique_identifier'):
            response.set_cookie('unique_identifier', request.unique_identifier, max_age=365 * 24 * 60 * 60)  # 1 year
        return response
