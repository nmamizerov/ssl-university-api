import logging
from rest_framework.permissions import BasePermission
from simulators.models import Simulator
from backend.helpers import STATISTIC_ACTIONS

class StatisticPermissions(BasePermission):

    def has_permission(self, request, view):
        if view.action in STATISTIC_ACTIONS:
            return True
        if view.params.get("simulator"):
            group = Simulator.objects.filter(id=view.params.get("simulator")).first().group
            if group:
                return group.owner == request.user
        elif request.data.get("simulator"):
            group = Simulator.objects.filter(id=request.data.get("simulator")).first().group
            if group:
                return group.owner == request.user
        return False
