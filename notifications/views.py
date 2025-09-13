from django.http import request
from backend.application_viewset import ApplicationReadOnlyViewSet
from simulators.models import SimulatorUser
from .serializers import NotificationSerializer
from rest_framework import mixins
from .models import Notification
import logging
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger("django.server")
# Create your views here.

class NotificationViewSet(ApplicationReadOnlyViewSet, mixins.CreateModelMixin):
    pagination_class = None
    serializer_class = NotificationSerializer

    @action(detail=True, methods=["post"])
    def score(self, request, *args, **kwargs):
        if not 'score' in request.data:
            return Response({"score": "это обязательно"}, status=status.HTTP_400_BAD_REQUEST)
        notification = self.get_object()
        notification.score = int(request.data['score'])
        notification.user.balance = notification.user.balance + int(request.data['score'])
        notification.user.save()
        notification.save()
        return Response()
    
    def get_queryset(self):
        queryset = []
        if 'place' in self.params:
            queryset = Notification.objects.filter(answer__place__id=int(self.params.get('place')), to_user=self.request.user)
        else:
            queryset = Notification.objects.filter(to_user=self.request.user)
        if 'type' in self.params:
            queryset = queryset.filter(type=self.params['type'])
        return queryset
