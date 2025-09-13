
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from backend.application_viewset import AdminApplicationViewSet, ReadOnlyViewSet
from backend.helpers import SAFE_ACTIONS
from lessons.models import Lesson
from pages.models import Page, UserPageProgress
from .permissions import StatisticPermissions
from .serializers import  MainInfoStatisticSerializer, MainUserStatisticSerializer, LessonInfoStatisticSerializer, PageUserStatisticSerializer
from simulators.models import Simulator, SimulatorUser
from backend.application_pagination import ApplicationPagination

class AdminStatisticViewSet(AdminApplicationViewSet):
    
    def get_serializer_class(self):
        if self.action == "main_info_statistic":
            return MainInfoStatisticSerializer
        if self.action == "lesson_info_statistic":
            return LessonInfoStatisticSerializer
        if self.action == 'main_users_statistic':
            return MainUserStatisticSerializer
        if self.action == 'pages_statistic':
            return PageUserStatisticSerializer
    
    def get_queryset(self):
        queryset = []
        if self.action in ("main_info_statistic", 'main_users_statistic'):
            queryset = Simulator.objects.filter(group__owner=self.request.user)
        elif self.action == "lesson_info_statistic":
            queryset = Lesson.objects.filter(simulator__group__owner=self.request.user)
        elif self.action == 'pages_statistic':
            queryset = Page.objects.filter(lesson__simulator__id=self.params['simulator'])
        return queryset

    @action(detail=True, methods=["GET"])
    def main_info_statistic(self, request, *args, **kwargs):
        return super().retrieve(request)

    @action(detail=True, methods=["GET"])
    def lesson_info_statistic(self, request, *args, **kwargs):
        return super().retrieve(request)
    
    @action(detail=True, methods={"GET"})
    def main_users_statistic(self, request, *args, **kwargs):
        return super().retrieve(request)

    @action(detail=False, methods={"GET"})
    def pages_statistic(self, request, *args, **kwargs):
        return super().list(request)
        
