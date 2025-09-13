from rest_framework.permissions import BasePermission
from simulator_groups.models import SimulatorGroup
from backend.helpers import SAFE_ACTIONS

import logging


logger = logging.getLogger("django.server")

class GroupPermissions(BasePermission):

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user