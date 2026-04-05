from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """
    Write access: session owner only.
    Read access: owner always; others only if session is public.
    """
    def has_object_permission(self, request, view, obj):
        if request.user == obj.user:
            return True
        if request.method in SAFE_METHODS:
            return obj.is_public and not obj.is_discarded
        return False
