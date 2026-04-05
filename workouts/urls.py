from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import WorkoutSessionViewSet

router = SimpleRouter()
router.register('', WorkoutSessionViewSet, basename='workout')

urlpatterns = [
    path('', include(router.urls)),
]
