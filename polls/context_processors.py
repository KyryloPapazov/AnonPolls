# context_processors.py

def cookies_accepted(request):
    return {'cookies_accepted': request.COOKIES.get('cookies_accepted', False)}