# authentication/permissions.py

from functools import wraps

from ninja.errors import HttpError


def permission_required(permission):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user.has_perm(permission):
                raise HttpError(
                    403,
                    "You do not have permission to perform this action.",
                )

            return func(request, *args, **kwargs)

        return wrapper

    return decorator