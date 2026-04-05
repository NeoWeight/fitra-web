from django.db import transaction
from rest_framework import serializers

from exercises.serializers import ExerciseSerializer
from .models import WorkoutExercise, WorkoutSession, WorkoutSet


class WorkoutSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutSet
        fields = [
            'id', 'set_number', 'reps', 'weight_kg', 'rir',
            'set_type', 'duration_seconds', 'distance_meters', 'is_completed',
        ]

    def validate_rir(self, value):
        if value is not None and value > 10:
            raise serializers.ValidationError('RIR must be between 0 and 10.')
        return value


class WorkoutExerciseSerializer(serializers.ModelSerializer):
    sets = WorkoutSetSerializer(many=True, required=False, default=list)
    exercise_detail = ExerciseSerializer(source='exercise', read_only=True)
    exercise_id = serializers.PrimaryKeyRelatedField(
        source='exercise',
        queryset=__import__('exercises.models', fromlist=['Exercise']).Exercise.objects.filter(is_active=True),
        write_only=True,
    )

    class Meta:
        model = WorkoutExercise
        fields = ['id', 'exercise_id', 'exercise_detail', 'order', 'notes', 'sets']


class WorkoutSessionSerializer(serializers.ModelSerializer):
    workout_exercises = WorkoutExerciseSerializer(many=True, required=False, default=list)
    exercise_count = serializers.SerializerMethodField()
    set_count = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutSession
        fields = [
            'id', 'title', 'notes', 'started_at', 'finished_at',
            'is_public', 'is_discarded', 'workout_exercises',
            'exercise_count', 'set_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['is_discarded', 'created_at', 'updated_at']

    def get_exercise_count(self, obj):
        return obj.workout_exercises.count()

    def get_set_count(self, obj):
        return WorkoutSet.objects.filter(workout_exercise__session=obj).count()

    def _generate_title(self, user):
        count = WorkoutSession.objects.filter(user=user).count()
        return f'Workout {count + 1}'

    @transaction.atomic
    def create(self, validated_data):
        exercises_data = validated_data.pop('workout_exercises', [])
        user = self.context['request'].user

        if not validated_data.get('title'):
            validated_data['title'] = self._generate_title(user)

        session = WorkoutSession.objects.create(user=user, **validated_data)
        self._create_exercises(session, exercises_data)
        return session

    @transaction.atomic
    def update(self, instance, validated_data):
        exercises_data = validated_data.pop('workout_exercises', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if exercises_data is not None:
            self._sync_exercises(instance, exercises_data)

        return instance

    def _create_exercises(self, session, exercises_data):
        for ex_data in exercises_data:
            sets_data = ex_data.pop('sets', [])
            workout_exercise = WorkoutExercise.objects.create(session=session, **ex_data)
            for set_data in sets_data:
                WorkoutSet.objects.create(workout_exercise=workout_exercise, **set_data)

    def _sync_exercises(self, session, exercises_data):
        existing_ids = set(session.workout_exercises.values_list('id', flat=True))
        submitted_ids = {ex.get('id') for ex in exercises_data if ex.get('id')}

        # Delete removed exercises
        session.workout_exercises.filter(id__in=existing_ids - submitted_ids).delete()

        for ex_data in exercises_data:
            sets_data = ex_data.pop('sets', [])
            ex_id = ex_data.pop('id', None)

            if ex_id:
                workout_exercise = WorkoutExercise.objects.get(id=ex_id, session=session)
                for attr, value in ex_data.items():
                    setattr(workout_exercise, attr, value)
                workout_exercise.save()
            else:
                workout_exercise = WorkoutExercise.objects.create(session=session, **ex_data)

            self._sync_sets(workout_exercise, sets_data)

    def _sync_sets(self, workout_exercise, sets_data):
        existing_ids = set(workout_exercise.sets.values_list('id', flat=True))
        submitted_ids = {s.get('id') for s in sets_data if s.get('id')}

        workout_exercise.sets.filter(id__in=existing_ids - submitted_ids).delete()

        for set_data in sets_data:
            set_id = set_data.pop('id', None)
            if set_id:
                workout_set = WorkoutSet.objects.get(id=set_id, workout_exercise=workout_exercise)
                for attr, value in set_data.items():
                    setattr(workout_set, attr, value)
                workout_set.save()
            else:
                WorkoutSet.objects.create(workout_exercise=workout_exercise, **set_data)
