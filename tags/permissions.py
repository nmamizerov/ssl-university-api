from rest_framework.permissions import BasePermission
from simulator_groups.models import SimulatorGroup
from backend.helpers import SAFE_ACTIONS
from simulators.models import Simulator


class TagPermissions(BasePermission):
    def has_permission(self, request, view):
        if view.action in SAFE_ACTIONS:
            return True
        if view.params.get("group"):
            group = SimulatorGroup.objects.filter(id=view.params.get("group")).first()
            if group:
                return group.owner == request.user
        elif request.data.get("group"):
            group = SimulatorGroup.objects.filter(id=request.data.get("group")).first()
            if group:
                return group.owner == request.user
        elif view.params.get('simulator_group'):
            simulator = Simulator.objects.filter(id=view.params.get("simulator_group")).first()
            if simulator:
                return simulator.group.owner == request.user
        return False
