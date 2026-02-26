from functools import wraps

from flask import redirect, request, session, url_for


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        if user_id is None:
            next_url = request.full_path or request.path or url_for('home')

            # Avoid storing a trailing '?' when there is no query string
            if next_url.endswith('?'):
                next_url = next_url[:-1]

            # Only store app-internal paths
            if not next_url.startswith('/'):
                next_url = url_for('home')

            session['next_url'] = next_url
            return redirect(url_for('login'))

        return fn(*args, **kwargs)

    return wrapper
