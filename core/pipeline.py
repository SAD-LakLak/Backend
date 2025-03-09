def get_avatar(backend, user, response, *args, **kwargs):

    if backend.name == 'google-oauth2':
        if response.get('picture'):
            user.avatar_url = response['picture']
            user.save()
    return None