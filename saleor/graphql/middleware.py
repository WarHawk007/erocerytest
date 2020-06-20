from typing import Optional

from django.contrib.auth.models import AnonymousUser
from django.shortcuts import reverse
from django.utils.functional import SimpleLazyObject
from graphene_django.settings import graphene_settings
from graphql_jwt.middleware import JSONWebTokenMiddleware

from ..account.models import ServiceAccount


class CustomCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "*"

        # Code to be executed for each request/response after
        # the view is called.

        return response

def jwt_middleware(get_response):
    """Authenticate a user using JWT and ignore the session-based authentication.

    This middleware resets authentication made by any previous middlewares
    and authenticates the user
    with graphql_jwt.middleware.JSONWebTokenMiddleware.
    """
    # Disable warnings for django-graphene-jwt
    graphene_settings.MIDDLEWARE.append(JSONWebTokenMiddleware)
    jwt_middleware_inst = JSONWebTokenMiddleware(get_response=get_response)
    graphene_settings.MIDDLEWARE.remove(JSONWebTokenMiddleware)

    def middleware(request):
        if request.path == reverse("api"):
            # clear user authenticated by AuthenticationMiddleware
            request._cached_user = AnonymousUser()
            request.user = AnonymousUser()

            # authenticate using JWT middleware
            jwt_middleware_inst.process_request(request)
        return get_response(request)

    return middleware


def open_access_middleware(get_response):
    def middleware(request):
        response = get_response(request)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "*"
        return response
    return middleware


def get_service_account(auth_token) -> Optional[ServiceAccount]:
    qs = ServiceAccount.objects.filter(tokens__auth_token=auth_token, is_active=True)
    return qs.first()


def service_account_middleware(get_response):

    service_account_auth_header = "HTTP_AUTHORIZATION"
    prefix = "bearer"

    def middleware(request):
        if request.path == reverse("api"):
            request.service_account = None
            auth = request.META.get(service_account_auth_header, "").split()
            if len(auth) == 2:
                auth_prefix, auth_token = auth
                if auth_prefix.lower() == prefix:
                    request.service_account = SimpleLazyObject(
                        lambda: get_service_account(auth_token)
                    )
        return get_response(request)

    return middleware
