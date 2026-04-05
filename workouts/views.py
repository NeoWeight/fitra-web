from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import WorkoutSession
from .permissions import IsOwnerOrReadOnly
from .serializers import WorkoutSessionSerializer


class WorkoutSessionViewSet(ModelViewSet):
    serializer_class = WorkoutSessionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        user = self.request.user

        # Detail view: owner sees all their sessions, others see only public
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'discard']:
            if user.is_authenticated:
                return WorkoutSession.objects.filter(
                    is_discarded=False
                ).select_related('user').prefetch_related(
                    'workout_exercises__exercise',
                    'workout_exercises__sets',
                )
            return WorkoutSession.objects.filter(
                is_public=True, is_discarded=False
            ).select_related('user').prefetch_related(
                'workout_exercises__exercise',
                'workout_exercises__sets',
            )

        # List view: own finished, non-discarded sessions only
        if user.is_authenticated:
            return WorkoutSession.objects.filter(
                user=user,
                is_discarded=False,
                finished_at__isnull=False,
            ).select_related('user').prefetch_related(
                'workout_exercises__exercise',
                'workout_exercises__sets',
            )
        return WorkoutSession.objects.none()

    def create(self, request, *args, **kwargs):
        # Enforce one active workout at a time
        active = WorkoutSession.objects.filter(
            user=request.user,
            finished_at__isnull=True,
            is_discarded=False,
        ).first()
        if active:
            return Response(
                {
                    'detail': 'You already have an active workout.',
                    'active_workout_id': active.id,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        session = self.get_object()
        if not session.is_finished:
            return Response(
                {'detail': 'Cannot delete an in-progress workout. Use discard instead.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def active(self, request):
        session = WorkoutSession.objects.filter(
            user=request.user,
            finished_at__isnull=True,
            is_discarded=False,
        ).prefetch_related(
            'workout_exercises__exercise',
            'workout_exercises__sets',
        ).first()

        if not session:
            return Response({'detail': 'No active workout.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(session)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def discard(self, request, pk=None):
        session = self.get_object()

        if session.user != request.user:
            raise PermissionDenied()

        if session.is_finished:
            return Response(
                {'detail': 'Cannot discard a finished workout.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.utils import timezone
        session.is_discarded = True
        session.finished_at = timezone.now()
        session.save()

        return Response({'detail': 'Workout discarded.'}, status=status.HTTP_200_OK)
