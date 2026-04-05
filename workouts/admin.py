from django.contrib import admin

from .models import WorkoutExercise, WorkoutSession, WorkoutSet


class WorkoutExerciseInline(admin.TabularInline):
    model = WorkoutExercise
    extra = 0


class WorkoutSetInline(admin.TabularInline):
    model = WorkoutSet
    extra = 0


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'started_at', 'finished_at', 'is_public', 'is_discarded']
    list_filter = ['is_public', 'is_discarded']
    search_fields = ['title', 'user__username']
    inlines = [WorkoutExerciseInline]


@admin.register(WorkoutExercise)
class WorkoutExerciseAdmin(admin.ModelAdmin):
    list_display = ['session', 'exercise', 'order']
    inlines = [WorkoutSetInline]
