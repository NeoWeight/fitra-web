from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import EquipmentViewSet, ExerciseViewSet, MuscleGroupViewSet

# Sub-resources must be registered before the empty-prefix exercise viewset,
# otherwise the exercise detail pattern (^<pk>/$) intercepts them.
router = SimpleRouter()
router.register('muscle-groups', MuscleGroupViewSet, basename='muscle-group')
router.register('equipment', EquipmentViewSet, basename='equipment')
router.register('', ExerciseViewSet, basename='exercise')

urlpatterns = [
    path('', include(router.urls)),
]
