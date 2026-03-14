from rest_framework.permissions import BasePermission


class IsSeller(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "seller")


class IsOwnerProduct(BasePermission):
    
    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_authenticated and obj.seller_id == request.user.id)


class IsOrderParty(BasePermission):
    
    def has_object_permission(self, request, view, obj):
        u = request.user
        return bool(u and u.is_authenticated and (obj.buyer_id == u.id or obj.seller_id == u.id))