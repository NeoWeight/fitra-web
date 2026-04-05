from django.contrib import admin

from .models import Equipment, Exercise, MuscleGroup


@admin.register(MuscleGroup)
class MuscleGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'body_region']
    list_filter = ['body_region']


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'primary_muscle_group', 'equipment', 'is_active']
    list_filter = ['category', 'is_active', 'primary_muscle_group']
    search_fields = ['name']
    filter_horizontal = ['secondary_muscle_groups']
