from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from backend.application_viewset import AdminApplicationViewSet, ReadOnlyViewSet
from backend.helpers import SAFE_ACTIONS
from simulators.models import Simulator
from .models import Tag
from .serializers import AdminTagSerializer, TagSerializer
from .permissions import TagPermissions


class AdminTagsViewSet(AdminApplicationViewSet):
    serializer_class = AdminTagSerializer
    pagination_class = None
    permission_classes = [TagPermissions]

    def get_queryset(self):
        if self.params.get('group') and self.action not in SAFE_ACTIONS:
            queryset = Tag.objects.filter(group__id=self.params.get('group'))
        elif self.params.get('simulator_group') and self.action not in SAFE_ACTIONS:
            group = Simulator.objects.get(id=self.params.get('simulator_group')).group
            queryset = Tag.objects.filter(group=group)
        else:
            queryset = Tag.objects.all()
        return queryset


class TagsViewSet(ReadOnlyViewSet):
    serializer_class = TagSerializer
    pagination_class = None

    def get_queryset(self):
        return Tag.objects.filter(group__id=self.params.get('group'))
