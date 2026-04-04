from django.urls import path

from users.views import MeView, UserProfileView

urlpatterns = [
    path('me/', MeView.as_view(), name='user-me'),
    path('<str:username>/', UserProfileView.as_view(), name='user-profile'),
]
