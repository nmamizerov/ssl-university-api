from rest_framework.permissions import BasePermission
from simulator_groups.models import SimulatorGroup
from backend.helpers import SAFE_ACTIONS

import logging


logger = logging.getLogger("django.server")

class SimulatorPermissions(BasePermission):

    def has_permission(self, request, view):
        logger.info(view.action)
        if view.action in SAFE_ACTIONS:
            return True
        group = SimulatorGroup.objects.filter(id=view.params.get('group')).first()
        if group:
            return group.owner == request.user
        return False

    def has_object_permission(self, request, view, obj):
        return obj.group.owner == request.user