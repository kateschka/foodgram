from django.contrib.auth import get_user_model
from djoser.views import UserViewSet as DjoserUserViewSet

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from recipes.models import Tag
from .serializers import TagSerializer

User = get_user_model()


class UserViewSet(DjoserUserViewSet):

    def get_permissions(self):
        if self.action == 'set_avatar' or self.action == 'delete_avatar':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(['put'], detail=False, url_path='avatar')
    def set_avatar(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'avatar': serializer.data['avatar']},
            status=status.HTTP_200_OK
        )

    @action(['delete'], detail=False, url_path='avatar')
    def delete_avatar(self, request, *args, **kwargs):
        request.user.avatar = None
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ['get']
