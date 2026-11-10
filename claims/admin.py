from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from .models import Claim, ClaimItem


class AdministratorOnly:
    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)


admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class RestrictedUserAdmin(AdministratorOnly, UserAdmin):
    pass


@admin.register(Group)
class RestrictedGroupAdmin(AdministratorOnly, GroupAdmin):
    pass

class ItemInline(admin.TabularInline):
    model = ClaimItem
    extra = 0

@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ['number', 'document_date', 'branch', 'warehouse', 'status']
    list_filter = ['status', 'warehouse']
    search_fields = ['number', 'branch', 'reporter']
    readonly_fields = ['number', 'created_by', 'updated_by', 'created_at', 'updated_at']
    inlines = [ItemInline]

    # All claim writes go through the version-checked application form.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
