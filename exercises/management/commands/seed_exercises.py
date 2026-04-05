from django.core.management.base import BaseCommand

from exercises.models import Equipment, Exercise, MuscleGroup

MUSCLE_GROUPS = [
    ('Chest', 'chest'),
    ('Front Delts', 'shoulders'),
    ('Side Delts', 'shoulders'),
    ('Rear Delts', 'shoulders'),
    ('Biceps', 'arms'),
    ('Triceps', 'arms'),
    ('Forearms', 'arms'),
    ('Lats', 'back'),
    ('Traps', 'back'),
    ('Rhomboids', 'back'),
    ('Lower Back', 'back'),
    ('Quads', 'legs'),
    ('Hamstrings', 'legs'),
    ('Glutes', 'legs'),
    ('Calves', 'legs'),
    ('Hip Flexors', 'legs'),
    ('Abs', 'core'),
    ('Obliques', 'core'),
]

EQUIPMENT = [
    'Barbell',
    'Dumbbell',
    'Kettlebell',
    'Cable',
    'Machine',
    'Bodyweight',
    'Resistance Band',
    'EZ Bar',
    'Pull-up Bar',
    'Bench',
]

EXERCISES = [
    # Chest
    ('Bench Press', 'strength', 'Chest', ['Front Delts', 'Triceps'], 'Barbell'),
    ('Incline Bench Press', 'strength', 'Chest', ['Front Delts', 'Triceps'], 'Barbell'),
    ('Decline Bench Press', 'strength', 'Chest', ['Triceps'], 'Barbell'),
    ('Dumbbell Fly', 'strength', 'Chest', [], 'Dumbbell'),
    ('Cable Fly', 'strength', 'Chest', [], 'Cable'),
    ('Push Up', 'strength', 'Chest', ['Front Delts', 'Triceps'], 'Bodyweight'),
    ('Dip', 'strength', 'Chest', ['Triceps', 'Front Delts'], 'Bodyweight'),

    # Back
    ('Deadlift', 'strength', 'Lower Back', ['Glutes', 'Hamstrings', 'Traps'], 'Barbell'),
    ('Barbell Row', 'strength', 'Lats', ['Rhomboids', 'Biceps', 'Rear Delts'], 'Barbell'),
    ('Pull Up', 'strength', 'Lats', ['Biceps', 'Rhomboids'], 'Pull-up Bar'),
    ('Chin Up', 'strength', 'Lats', ['Biceps'], 'Pull-up Bar'),
    ('Lat Pulldown', 'strength', 'Lats', ['Biceps', 'Rhomboids'], 'Cable'),
    ('Seated Cable Row', 'strength', 'Rhomboids', ['Lats', 'Biceps', 'Rear Delts'], 'Cable'),
    ('Dumbbell Row', 'strength', 'Lats', ['Rhomboids', 'Biceps'], 'Dumbbell'),
    ('Face Pull', 'strength', 'Rear Delts', ['Traps', 'Rhomboids'], 'Cable'),

    # Shoulders
    ('Overhead Press', 'strength', 'Front Delts', ['Side Delts', 'Triceps'], 'Barbell'),
    ('Dumbbell Shoulder Press', 'strength', 'Front Delts', ['Side Delts', 'Triceps'], 'Dumbbell'),
    ('Lateral Raise', 'strength', 'Side Delts', [], 'Dumbbell'),
    ('Front Raise', 'strength', 'Front Delts', [], 'Dumbbell'),
    ('Reverse Fly', 'strength', 'Rear Delts', ['Rhomboids'], 'Dumbbell'),
    ('Shrug', 'strength', 'Traps', [], 'Barbell'),

    # Arms
    ('Barbell Curl', 'strength', 'Biceps', ['Forearms'], 'Barbell'),
    ('Dumbbell Curl', 'strength', 'Biceps', ['Forearms'], 'Dumbbell'),
    ('Hammer Curl', 'strength', 'Biceps', ['Forearms'], 'Dumbbell'),
    ('Preacher Curl', 'strength', 'Biceps', [], 'EZ Bar'),
    ('Tricep Pushdown', 'strength', 'Triceps', [], 'Cable'),
    ('Skull Crusher', 'strength', 'Triceps', [], 'EZ Bar'),
    ('Overhead Tricep Extension', 'strength', 'Triceps', [], 'Dumbbell'),
    ('Close Grip Bench Press', 'strength', 'Triceps', ['Chest', 'Front Delts'], 'Barbell'),

    # Legs
    ('Squat', 'strength', 'Quads', ['Glutes', 'Hamstrings'], 'Barbell'),
    ('Front Squat', 'strength', 'Quads', ['Glutes'], 'Barbell'),
    ('Leg Press', 'strength', 'Quads', ['Glutes', 'Hamstrings'], 'Machine'),
    ('Romanian Deadlift', 'strength', 'Hamstrings', ['Glutes', 'Lower Back'], 'Barbell'),
    ('Leg Curl', 'strength', 'Hamstrings', [], 'Machine'),
    ('Leg Extension', 'strength', 'Quads', [], 'Machine'),
    ('Bulgarian Split Squat', 'strength', 'Quads', ['Glutes', 'Hamstrings'], 'Dumbbell'),
    ('Hip Thrust', 'strength', 'Glutes', ['Hamstrings'], 'Barbell'),
    ('Calf Raise', 'strength', 'Calves', [], 'Machine'),
    ('Lunges', 'strength', 'Quads', ['Glutes', 'Hamstrings'], 'Dumbbell'),

    # Core
    ('Plank', 'strength', 'Abs', ['Obliques'], 'Bodyweight'),
    ('Crunch', 'strength', 'Abs', [], 'Bodyweight'),
    ('Russian Twist', 'strength', 'Obliques', ['Abs'], 'Bodyweight'),
    ('Leg Raise', 'strength', 'Abs', ['Hip Flexors'], 'Bodyweight'),
    ('Ab Wheel Rollout', 'strength', 'Abs', ['Obliques', 'Lats'], 'Bodyweight'),
    ('Cable Crunch', 'strength', 'Abs', [], 'Cable'),

    # Cardio
    ('Treadmill Run', 'cardio', 'Quads', ['Hamstrings', 'Glutes', 'Calves'], None),
    ('Rowing Machine', 'cardio', 'Lats', ['Rhomboids', 'Biceps', 'Quads'], 'Machine'),
    ('Stationary Bike', 'cardio', 'Quads', ['Hamstrings', 'Glutes', 'Calves'], 'Machine'),
    ('Jump Rope', 'cardio', 'Calves', ['Quads', 'Abs'], 'Bodyweight'),
]


class Command(BaseCommand):
    help = 'Seed the database with a base set of exercises'

    def handle(self, *args, **options):
        self.stdout.write('Seeding muscle groups...')
        muscle_map = {}
        for name, region in MUSCLE_GROUPS:
            obj, _ = MuscleGroup.objects.get_or_create(name=name, defaults={'body_region': region})
            muscle_map[name] = obj

        self.stdout.write('Seeding equipment...')
        equipment_map = {}
        for name in EQUIPMENT:
            obj, _ = Equipment.objects.get_or_create(name=name)
            equipment_map[name] = obj

        self.stdout.write('Seeding exercises...')
        created = 0
        for name, category, primary, secondaries, equip_name in EXERCISES:
            equipment = equipment_map[equip_name] if equip_name else None
            exercise, was_created = Exercise.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'primary_muscle_group': muscle_map[primary],
                    'equipment': equipment,
                },
            )
            if was_created:
                for s in secondaries:
                    exercise.secondary_muscle_groups.add(muscle_map[s])
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. {created} exercises created ({len(EXERCISES) - created} already existed).'
        ))
