from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile
from .forms import CustomUserCreationForm, CustomUserChangeForm

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ['email', 'username', 'is_email_verified', 'is_staff', 'is_active']
    list_filter = ['is_email_verified', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Verification Status', {'fields': ('is_email_verified', 'verification_token')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Verification Status', {'fields': ('is_email_verified', 'verification_token')}),
    )
    search_fields = ('email', 'username')
    ordering = ('email',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_role', 'target_role', 'experience_level', 'created_at')
    search_fields = ('user__email', 'user__username', 'current_role', 'target_role')
    list_filter = ('experience_level', 'created_at')

admin.site.register(User, CustomUserAdmin)
