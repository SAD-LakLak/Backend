from rest_framework.permissions import BasePermission

class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'customer'

class IsSupplier(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'supplier'

class IsPackageCombinator(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'package_combinator'

class IsDeliveryPersonnel(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'delivery_personnel'

class IsSupervisor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'supervisor'
    

