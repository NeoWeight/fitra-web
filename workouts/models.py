from django.conf import settings
from django.db import models


class WorkoutSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workout_sessions',
    )
    title = models.CharField(max_length=200, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    is_public = models.BooleanField(default=True)
    is_discarded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user.username} — {self.title}"

    @property
    def is_finished(self):
        return self.finished_at is not None


class WorkoutExercise(models.Model):
    session = models.ForeignKey(
        WorkoutSession,
        on_delete=models.CASCADE,
        related_name='workout_exercises',
    )
    exercise = models.ForeignKey(
        'exercises.Exercise',
        on_delete=models.PROTECT,
        related_name='workout_exercises',
    )
    order = models.PositiveSmallIntegerField(default=0)
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.session} — {self.exercise.name}"


class WorkoutSet(models.Model):
    SET_TYPE_CHOICES = [
        ('normal', 'Normal'),
        ('warmup', 'Warm-up'),
        ('drop', 'Drop Set'),
        ('failure', 'To Failure'),
    ]
    workout_exercise = models.ForeignKey(
        WorkoutExercise,
        on_delete=models.CASCADE,
        related_name='sets',
    )
    set_number = models.PositiveSmallIntegerField()
    reps = models.PositiveSmallIntegerField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    rir = models.PositiveSmallIntegerField(null=True, blank=True)  # Reps in Reserve (0-10)
    set_type = models.CharField(max_length=10, choices=SET_TYPE_CHOICES, default='normal')
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    distance_meters = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['set_number']

    def __str__(self):
        return f"{self.workout_exercise} — Set {self.set_number}"
