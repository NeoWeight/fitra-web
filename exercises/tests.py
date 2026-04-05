from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Equipment, Exercise, MuscleGroup

User = get_user_model()

EXERCISES_URL = '/api/v1/exercises/'
MUSCLE_GROUPS_URL = '/api/v1/exercises/muscle-groups/'
EQUIPMENT_URL = '/api/v1/exercises/equipment/'


def exercise_url(pk):
    return f'/api/v1/exercises/{pk}/'


class ExerciseSetupMixin:
    def setUp(self):
        self.chest = MuscleGroup.objects.create(name='Chest', body_region='upper')
        self.triceps = MuscleGroup.objects.create(name='Triceps', body_region='upper')
        self.barbell = Equipment.objects.create(name='Barbell')
        self.bench_press = Exercise.objects.create(
            name='Bench Press',
            category='strength',
            primary_muscle_group=self.chest,
            equipment=self.barbell,
        )
        self.bench_press.secondary_muscle_groups.add(self.triceps)
        self.squat = Exercise.objects.create(
            name='Squat',
            category='strength',
            primary_muscle_group=MuscleGroup.objects.create(name='Quads', body_region='lower'),
            equipment=self.barbell,
        )
        self.run = Exercise.objects.create(
            name='Treadmill Run',
            category='cardio',
            primary_muscle_group=MuscleGroup.objects.create(name='Calves', body_region='lower'),
        )
        self.inactive = Exercise.objects.create(
            name='Inactive Exercise',
            category='strength',
            primary_muscle_group=self.chest,
            is_active=False,
        )


class ExerciseListTests(ExerciseSetupMixin, APITestCase):
    def test_list_returns_active_exercises_only(self):
        response = self.client.get(EXERCISES_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [e['name'] for e in response.data['results']]
        self.assertIn('Bench Press', names)
        self.assertNotIn('Inactive Exercise', names)

    def test_list_unauthenticated_allowed(self):
        response = self.client.get(EXERCISES_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_category(self):
        response = self.client.get(EXERCISES_URL, {'category': 'cardio'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [e['name'] for e in response.data['results']]
        self.assertIn('Treadmill Run', names)
        self.assertNotIn('Bench Press', names)

    def test_filter_by_muscle_group(self):
        response = self.client.get(EXERCISES_URL, {'muscle_group': 'Chest'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [e['name'] for e in response.data['results']]
        self.assertIn('Bench Press', names)
        self.assertNotIn('Squat', names)

    def test_search_by_name(self):
        response = self.client.get(EXERCISES_URL, {'search': 'bench'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [e['name'] for e in response.data['results']]
        self.assertIn('Bench Press', names)
        self.assertNotIn('Squat', names)


class ExerciseDetailTests(ExerciseSetupMixin, APITestCase):
    def test_retrieve_exercise(self):
        response = self.client.get(exercise_url(self.bench_press.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Bench Press')
        self.assertEqual(response.data['primary_muscle_group']['name'], 'Chest')
        self.assertEqual(len(response.data['secondary_muscle_groups']), 1)
        self.assertEqual(response.data['secondary_muscle_groups'][0]['name'], 'Triceps')
        self.assertEqual(response.data['equipment']['name'], 'Barbell')

    def test_retrieve_inactive_returns_404(self):
        response = self.client.get(exercise_url(self.inactive.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ExerciseWriteTests(ExerciseSetupMixin, APITestCase):
    def test_non_admin_cannot_post(self):
        user = User.objects.create_user(email='u@u.com', username='u', password='pass1234')
        self.client.force_authenticate(user=user)
        response = self.client.post(EXERCISES_URL, {'name': 'New Exercise'})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_unauthenticated_cannot_post(self):
        response = self.client.post(EXERCISES_URL, {'name': 'New Exercise'})
        self.assertIn(response.status_code, [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        ])


class MuscleGroupTests(ExerciseSetupMixin, APITestCase):
    def test_list_muscle_groups(self):
        response = self.client.get(MUSCLE_GROUPS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [m['name'] for m in response.data['results']]
        self.assertIn('Chest', names)
        self.assertIn('Triceps', names)


class EquipmentTests(ExerciseSetupMixin, APITestCase):
    def test_list_equipment(self):
        response = self.client.get(EQUIPMENT_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [e['name'] for e in response.data['results']]
        self.assertIn('Barbell', names)
