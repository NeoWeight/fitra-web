from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Equipment, Exercise, MuscleGroup
from .serializers import EquipmentSerializer, ExerciseSerializer, MuscleGroupSerializer


class ExerciseViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name']
    ordering_fields = ['name', 'category']

    def get_queryset(self):
        qs = Exercise.objects.filter(is_active=True).select_related(
            'primary_muscle_group', 'equipment'
        ).prefetch_related('secondary_muscle_groups')

        muscle_group = self.request.query_params.get('muscle_group')
        if muscle_group:
            qs = qs.filter(primary_muscle_group__name__icontains=muscle_group)

        return qs


class MuscleGroupViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MuscleGroupSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = MuscleGroup.objects.all().order_by('body_region', 'name')


class EquipmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EquipmentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Equipment.objects.all().order_by('name')
