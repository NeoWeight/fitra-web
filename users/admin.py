from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, UserProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'is_staff', 'date_joined']
    ordering = ['-date_joined']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_public', 'created_at']
