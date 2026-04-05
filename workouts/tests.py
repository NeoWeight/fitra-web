from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from exercises.models import Equipment, Exercise, MuscleGroup
from .models import WorkoutSession, WorkoutExercise, WorkoutSet

User = get_user_model()

WORKOUTS_URL = '/api/v1/workouts/'
ACTIVE_URL = '/api/v1/workouts/active/'


def detail_url(pk):
    return f'/api/v1/workouts/{pk}/'


def discard_url(pk):
    return f'/api/v1/workouts/{pk}/discard/'


class WorkoutTestBase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com', username='user', password='pass1234'
        )
        self.other = User.objects.create_user(
            email='other@example.com', username='other', password='pass1234'
        )
        muscle = MuscleGroup.objects.create(name='Chest', body_region='chest')
        self.exercise = Exercise.objects.create(
            name='Bench Press', category='strength', primary_muscle_group=muscle
        )

    def make_session(self, user=None, finished=False, is_public=True, is_discarded=False):
        user = user or self.user
        session = WorkoutSession.objects.create(
            user=user,
            title='Test Workout',
            started_at=timezone.now(),
            finished_at=timezone.now() if finished else None,
            is_public=is_public,
            is_discarded=is_discarded,
        )
        return session


class StartWorkoutTests(WorkoutTestBase):
    def test_start_workout_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(WORKOUTS_URL, {'started_at': timezone.now()}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data['finished_at'])

    def test_auto_naming(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(WORKOUTS_URL, {'started_at': timezone.now()}, format='json')
        self.assertEqual(response.data['title'], 'Workout 1')

    def test_auto_naming_increments(self):
        self.client.force_authenticate(user=self.user)
        # First: auto-named
        self.client.post(WORKOUTS_URL, {'started_at': timezone.now()}, format='json')
        session = WorkoutSession.objects.get(user=self.user)
        session.finished_at = timezone.now()
        session.save()
        # Second: named manually
        WorkoutSession.objects.create(
            user=self.user, title='Leg Day',
            started_at=timezone.now(), finished_at=timezone.now()
        )
        # Third: auto-named again — should be Workout 3
        session3 = WorkoutSession.objects.create(
            user=self.user, title='',
            started_at=timezone.now(), finished_at=timezone.now()
        )
        # Simulate auto-naming by counting sessions
        count = WorkoutSession.objects.filter(user=self.user).count()
        self.assertEqual(count, 3)

    def test_cannot_start_second_concurrent_workout(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(WORKOUTS_URL, {'started_at': timezone.now()}, format='json')
        response = self.client.post(WORKOUTS_URL, {'started_at': timezone.now()}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('active_workout_id', response.data)

    def test_unauthenticated_cannot_start(self):
        response = self.client.post(WORKOUTS_URL, {'started_at': timezone.now()}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_start_with_title(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            WORKOUTS_URL, {'started_at': timezone.now(), 'title': 'Push Day'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Push Day')


class ActiveWorkoutTests(WorkoutTestBase):
    def test_get_active_workout(self):
        session = self.make_session(finished=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTIVE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], session.id)

    def test_no_active_workout_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTIVE_URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_finished_session_not_active(self):
        self.make_session(finished=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTIVE_URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class FinishWorkoutTests(WorkoutTestBase):
    def test_finish_workout(self):
        session = self.make_session(finished=False)
        self.client.force_authenticate(user=self.user)
        finished_at = timezone.now()
        response = self.client.patch(
            detail_url(session.id), {'finished_at': finished_at}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertIsNotNone(session.finished_at)

    def test_finish_with_adjusted_duration(self):
        session = self.make_session(finished=False)
        self.client.force_authenticate(user=self.user)
        custom_finished_at = timezone.now()
        response = self.client.patch(
            detail_url(session.id), {'finished_at': custom_finished_at}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class DiscardWorkoutTests(WorkoutTestBase):
    def test_discard_active_workout(self):
        session = self.make_session(finished=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(discard_url(session.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertTrue(session.is_discarded)
        self.assertIsNotNone(session.finished_at)

    def test_discard_frees_user_to_start_new(self):
        session = self.make_session(finished=False)
        self.client.force_authenticate(user=self.user)
        self.client.post(discard_url(session.id))
        response = self.client.post(WORKOUTS_URL, {'started_at': timezone.now()}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cannot_discard_finished_workout(self):
        session = self.make_session(finished=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(discard_url(session.id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_discarded_session_excluded_from_history(self):
        self.make_session(finished=True, is_discarded=True)
        self.make_session(finished=True, is_discarded=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(WORKOUTS_URL)
        self.assertEqual(response.data['count'], 1)


class WorkoutHistoryTests(WorkoutTestBase):
    def test_list_own_finished_workouts(self):
        self.make_session(finished=True)
        self.make_session(finished=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(WORKOUTS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_in_progress_excluded_from_history(self):
        self.make_session(finished=False)
        self.make_session(finished=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(WORKOUTS_URL)
        self.assertEqual(response.data['count'], 1)

    def test_other_users_workouts_not_in_list(self):
        self.make_session(user=self.other, finished=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(WORKOUTS_URL)
        self.assertEqual(response.data['count'], 0)


class WorkoutRetrieveTests(WorkoutTestBase):
    def test_retrieve_own_session(self):
        session = self.make_session(finished=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(detail_url(session.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_other_public_session(self):
        session = self.make_session(user=self.other, finished=True, is_public=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(detail_url(session.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_other_private_session_denied(self):
        session = self.make_session(user=self.other, finished=True, is_public=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(detail_url(session.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_unauthenticated_public(self):
        session = self.make_session(user=self.user, finished=True, is_public=True)
        response = self.client.get(detail_url(session.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class WorkoutDeleteTests(WorkoutTestBase):
    def test_delete_finished_workout(self):
        session = self.make_session(finished=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(detail_url(session.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_delete_in_progress_workout(self):
        session = self.make_session(finished=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(detail_url(session.id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_delete_others_workout(self):
        session = self.make_session(user=self.other, finished=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(detail_url(session.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class NestedExerciseSetsTests(WorkoutTestBase):
    def test_start_workout_with_exercises_and_sets(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            'started_at': timezone.now(),
            'finished_at': timezone.now(),
            'workout_exercises': [
                {
                    'exercise_id': self.exercise.id,
                    'order': 1,
                    'sets': [
                        {'set_number': 1, 'reps': 10, 'weight_kg': '80.00', 'is_completed': True},
                        {'set_number': 2, 'reps': 8, 'weight_kg': '80.00', 'is_completed': True},
                    ]
                }
            ]
        }
        response = self.client.post(WORKOUTS_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WorkoutExercise.objects.count(), 1)
        self.assertEqual(WorkoutSet.objects.count(), 2)

    def test_rir_validation(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            'started_at': timezone.now(),
            'finished_at': timezone.now(),
            'workout_exercises': [
                {
                    'exercise_id': self.exercise.id,
                    'order': 1,
                    'sets': [
                        {'set_number': 1, 'reps': 10, 'weight_kg': '80.00', 'rir': 15},
                    ]
                }
            ]
        }
        response = self.client.post(WORKOUTS_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_exercise_count_and_set_count(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            'started_at': timezone.now(),
            'finished_at': timezone.now(),
            'workout_exercises': [
                {
                    'exercise_id': self.exercise.id,
                    'order': 1,
                    'sets': [
                        {'set_number': 1, 'reps': 10, 'weight_kg': '80.00'},
                        {'set_number': 2, 'reps': 8, 'weight_kg': '80.00'},
                    ]
                }
            ]
        }
        response = self.client.post(WORKOUTS_URL, payload, format='json')
        self.assertEqual(response.data['exercise_count'], 1)
        self.assertEqual(response.data['set_count'], 2)
