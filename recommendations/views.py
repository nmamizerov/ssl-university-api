from django.shortcuts import render

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from backend.application_viewset import AdminApplicationViewSet, ReadOnlyViewSet
from backend.helpers import SAFE_ACTIONS
from simulators.models import Simulator
from .models import Recommendation
from .serializers import AdminRecommendationSerializer, RecommendationSerializer
from .permissions import RecommendationPermissions


class AdminRecommendationViewSet(AdminApplicationViewSet):
    serializer_class = AdminRecommendationSerializer
    pagination_class = None
    permission_classes = [RecommendationPermissions]

    def get_queryset(self):
        if self.params.get('group') and self.action not in SAFE_ACTIONS:
            queryset = Recommendation.objects.filter(group__id=self.params.get('group'))
        elif self.params.get('simulator_group') and self.action not in SAFE_ACTIONS:
            group = Simulator.objects.get(id=self.params.get('simulator_group')).group
            queryset = Recommendation.objects.filter(group=group)
        else:
            queryset = Recommendation.objects.all()
        return queryset


class RecommendationViewSet(ReadOnlyViewSet):
    serializer_class = RecommendationSerializer
    pagination_class = None

    def get_queryset(self):
        return Recommendation.objects.filter(group__id=self.params.get('group'))
