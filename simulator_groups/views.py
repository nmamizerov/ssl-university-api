from rest_framework import serializers
from backend.application_viewset import AdminApplicationViewSet
from simulator_groups.permissions import GroupPermissions
from .serializers import SimulatorGroupSerializer
from .models import SimulatorGroup
# Create your views here.


class AdminSimulatorGroupViewSet(AdminApplicationViewSet):
    pagination_class = None
    serializer_class = SimulatorGroupSerializer
    permission_classes = [GroupPermissions]

    def perform_destroy(self, instance):
        groups = SimulatorGroup.objects.filter(owner=self.request.user)
        if groups.count() == 1:
            raise serializers.ValidationError("Нельзя удалить единственную группу!")

        instance.delete()
    
    def get_queryset(self):
        return SimulatorGroup.objects.filter(owner=self.request.user)
