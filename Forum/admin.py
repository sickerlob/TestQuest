from django.contrib import admin
from .models import User, Role, ElementsControl, RoleAccess, PostFromUser


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'lastname', 'name', 'role', 'is_active')
    search_fields = ('email', 'lastname')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'role_name')

@admin.register(ElementsControl)
class ElementsControlAdmin(admin.ModelAdmin):
    list_display = ('id', 'element_name')

@admin.register(RoleAccess)
class RoleAccessAdmin(admin.ModelAdmin):
    list_display = ('id', 'role', 'element', 'can_create', 'can_read_all', 'can_update_own')

@admin.register(PostFromUser)
class PostFromUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner')