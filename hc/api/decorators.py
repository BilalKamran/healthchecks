import json
from functools import wraps

from django.contrib.auth.models import User
from django.http import JsonResponse
from hc.lib.jsonschema import ValidationError, validate


def error(msg, status=400):
    return JsonResponse({"error": msg}, status=status)


def check_api_key(f):
    @wraps(f)
    def wrapper(request, *args, **kwds):
        if "HTTP_X_API_KEY" in request.META:
            api_key = request.META["HTTP_X_API_KEY"]
        else:
            api_key = str(request.json.get("api_key", ""))

        if len(api_key) != 32:
            return error("missing api key", 401)

        try:
            request.user = User.objects.get(profile__api_key=api_key)
        except User.DoesNotExist:
            return error("wrong api key", 401)

        return f(request, *args, **kwds)

    return wrapper


def validate_json(schema=None):
    """ Parse request json and validate it against `schema`.

    Put the parsed result in `request.json`.
    If schema is None then only parse and don't validate.
    Supports  a limited subset of JSON schema spec.

    """

    def decorator(f):
        @wraps(f)
        def wrapper(request, *args, **kwds):
            if request.body:
                try:
                    request.json = json.loads(request.body.decode())
                except ValueError:
                    return error("could not parse request body")
            else:
                request.json = {}

            if schema:
                try:
                    validate(request.json, schema)
                except ValidationError as e:
                    return error("json validation error: %s" % e)

            return f(request, *args, **kwds)
        return wrapper
    return decorator
