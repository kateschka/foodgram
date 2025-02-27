from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import viewsets
from .serializers import UserSerializer

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
