from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
	def has_object_permission(self, request, view, obj):
		if request.method == 'GET' and (request.user.is_staff or request.user.is_superuser):
			return True
		return request.user == obj.user