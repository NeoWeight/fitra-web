from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound

from .serializers import RegisterSerializer, UserMeSerializer, UserSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserMeSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_object(self):
        return self.request.user


class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.select_related('profile')
    lookup_field = 'username'

    def get_object(self):
        user = generics.get_object_or_404(User, username=self.kwargs['username'])
        if not user.profile.is_public and self.request.user != user:
            raise NotFound()
        return user
