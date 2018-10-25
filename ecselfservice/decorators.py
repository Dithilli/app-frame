from functools import wraps
from flask import abort, current_app, redirect, request
from flask_login import current_user
from .models import Permission


def ssl_required(fn):
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        if current_app.config.get("SSL"):
            if request.is_secure:
                return fn(*args, **kwargs)
            else:
                secure_url = request.url.replace('http://', 'https://')
                current_app.logger.info(f"{request.url} {secure_url}")
                return redirect(secure_url)
        return fn(*args, **kwargs)
    return decorated_view


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                return current_app.login_manager.unauthorized()
                # abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    return permission_required(Permission.ADMIN)(f)


def read_required(f):
    return permission_required(Permission.READ)(f)


def write_required(f):
    return permission_required(Permission.WRITE)(f)
