from rest_framework.permissions import BasePermission
from lessons.models import Lesson
from backend.helpers import SAFE_ACTIONS
import logging
logger = logging.getLogger("django.server")

class PagePermissions(BasePermission):

    def has_permission(self, request, view):
        if view.action in SAFE_ACTIONS:
            return True
        if view.params.get("lesson"):
            lesson = Lesson.objects.filter(id=view.params.get("lesson")).first()
            if lesson:
                group = lesson.simulator.group
                if group:
                    return group.owner == request.user
        elif request.data.get("lesson"):
            lesson = Lesson.objects.filter(id=request.data.get("lesson")).first() 
            if lesson:
                group = lesson.simulator.group
                if group:
                    return group.owner == request.user
        return False

    def has_object_permission(self, request, view, obj):
        if obj.is_onboarding_for:
            return obj.is_onboarding_for.group.owner == request.user
        return obj.lesson.simulator.group.owner == request.user