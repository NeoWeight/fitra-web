from django.db import models


class MuscleGroup(models.Model):
    BODY_REGION_CHOICES = [
        ('chest', 'Chest'),
        ('back', 'Back'),
        ('shoulders', 'Shoulders'),
        ('arms', 'Arms'),
        ('core', 'Core'),
        ('legs', 'Legs'),
    ]
    name = models.CharField(max_length=100, unique=True)
    body_region = models.CharField(max_length=10, choices=BODY_REGION_CHOICES)

    def __str__(self):
        return self.name


class Equipment(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Exercise(models.Model):
    CATEGORY_CHOICES = [
        ('strength', 'Strength'),
        ('cardio', 'Cardio'),
        ('flexibility', 'Flexibility'),
        ('plyometrics', 'Plyometrics'),
    ]
    name = models.CharField(max_length=200, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    primary_muscle_group = models.ForeignKey(
        MuscleGroup,
        on_delete=models.PROTECT,
        related_name='primary_exercises',
    )
    secondary_muscle_groups = models.ManyToManyField(
        MuscleGroup,
        blank=True,
        related_name='secondary_exercises',
    )
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exercises',
    )
    instructions = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
