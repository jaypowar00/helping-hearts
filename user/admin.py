from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *


class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'name', 'phone', 'account_type', 'date_joined',)
    list_filter = ('account_type', )
    search_fields = ('email', 'name', 'phone',)
    filter_horizontal = ()
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password',)}),
        ('Personal Info', {'fields': ('name', 'address', 'phone', 'pincode', 'about',)}),
        ('Account_Type', {'fields': ('account_type',)})
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'username', 'password1', 'password2')}),
        ('Personal Info', {'fields': ('name', 'address', 'phone', 'pincode', 'about',)}),
        ('Account_Type', {'fields': ('account_type',)})
    )


class CustomAdmin(admin.ModelAdmin):
    list_display = ('get_email', 'get_username', 'get_name', 'get_phone',)
    search_fields = ('id__email', 'id__username', 'id__phone', 'id__name')

    def get_email(self, obj):
        return obj.id.email
    get_email.short_description = 'Email'

    def get_username(self, obj):
        return obj.id.username
    get_username.short_description = 'Username'

    def get_name(self, obj):
        return obj.id.name
    get_name.short_description = 'Name'

    def get_phone(self, obj):
        return obj.id.phone
    get_phone.short_description = 'Phone'


admin.site.register(User, UserAdmin)
admin.site.register(Patient, CustomAdmin)
admin.site.register(Hospital, CustomAdmin)
admin.site.register(VenProvider, CustomAdmin)
admin.site.register(CoWorker, CustomAdmin)
