from .services import is_moderator

def roles(request):
    return {'is_moderator': is_moderator(request.user)}
