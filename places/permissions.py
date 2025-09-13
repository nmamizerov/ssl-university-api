from pages.models import Page
from rest_framework.permissions import BasePermission
from lessons.models import Lesson
from backend.helpers import SAFE_ACTIONS
import logging
logger = logging.getLogger("django.server")

class PlacePermissions(BasePermission):

    def has_permission(self, request, view):
        if view.action in SAFE_ACTIONS:
            return True
        if view.params.get("page"):
            page = Page.objects.filter(id=view.params.get("page")).first()
            if page:
                group = page.lesson.simulator.group
                if group:
                    return group.owner == request.user
        elif request.data.get("page"):
            page = Page.objects.filter(id=request.data.get("page")).first() 
            if page:
                group = page.lesson.simulator.group
                if group:
                    return group.owner == request.user
        elif view.params.get('lesson'):
            lesson = Lesson.objects.filter(id=view.params.get("lesson")).first()
            if lesson:
                group = lesson.simulator.group
                if group:
                    return group.owner == request.user
        return False

    def has_object_permission(self, request, view, obj):
        if obj.page.is_onboarding_for:
            return obj.page.is_onboarding_for.group.owner == request.user    
        return obj.page.lesson.simulator.group.owner == request.user