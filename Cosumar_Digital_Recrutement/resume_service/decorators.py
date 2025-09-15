from django.core.exceptions import PermissionDenied
from functools import wraps
from django.http import JsonResponse
from rest_framework import status

def allow_roles(*role_names):
    """
    Decorator for views that checks whether a user is authenticated
    and has one of the required roles.
    Example: @allow_roles("admin", "admin_rh")
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return JsonResponse({
                    "error": "Vous devez être connecté pour accéder à cette ressource."
                }, status=status.HTTP_401_UNAUTHORIZED)

            if not hasattr(user, 'role') or user.role not in role_names:
                return JsonResponse({
                    "error": "Vous n'avez pas les permissions nécessaires pour accéder à cette ressource."
                }, status=status.HTTP_403_FORBIDDEN)

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def admin_required(view_func):
    """
    Decorator that requires admin role
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({
                "error": "Vous devez être connecté pour accéder à cette ressource."
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not hasattr(user, 'role') or user.role != 'admin':
            return JsonResponse({
                "error": "Accès réservé aux administrateurs."
            }, status=status.HTTP_403_FORBIDDEN)

        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_or_rh_required(view_func):
    """
    Decorator that requires admin or RH roles
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({
                "error": "Vous devez être connecté pour accéder à cette ressource."
            }, status=status.HTTP_401_UNAUTHORIZED)

        allowed_roles = ['admin', 'admin_rh', 'utilisateur_rh']
        if not hasattr(user, 'role') or user.role not in allowed_roles:
            return JsonResponse({
                "error": "Accès réservé aux administrateurs et personnel RH."
            }, status=status.HTTP_403_FORBIDDEN)

        return view_func(request, *args, **kwargs)
    return _wrapped_view

def exclude_utilisateur_role(view_func):
    """
    Decorator that excludes 'utilisateur' and 'responsable_de_service' roles from accessing the endpoint
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({
                "error": "Vous devez être connecté pour accéder à cette ressource."
            }, status=status.HTTP_401_UNAUTHORIZED)

        if hasattr(user, 'role') and user.role in ['utilisateur', 'responsable_de_service']:
            return JsonResponse({
                "error": "Vous n'avez pas les permissions nécessaires pour accéder à cette ressource."
            }, status=status.HTTP_403_FORBIDDEN)

        return view_func(request, *args, **kwargs)
    return _wrapped_view