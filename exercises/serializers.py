from rest_framework import serializers

from .models import Equipment, Exercise, MuscleGroup


class MuscleGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = MuscleGroup
        fields = ['id', 'name', 'body_region']


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ['id', 'name']


class ExerciseSerializer(serializers.ModelSerializer):
    primary_muscle_group = MuscleGroupSerializer(read_only=True)
    secondary_muscle_groups = MuscleGroupSerializer(many=True, read_only=True)
    equipment = EquipmentSerializer(read_only=True)

    class Meta:
        model = Exercise
        fields = [
            'id', 'name', 'category', 'primary_muscle_group',
            'secondary_muscle_groups', 'equipment', 'instructions',
        ]
