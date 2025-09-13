import logging

from rest_framework import status, viewsets
from django.shortcuts import get_object_or_404
from backend.application_viewset import AdminApplicationViewSet
from .serializers import AdminSimulatorSerializer, SimulatorSerializer
from .permissions import SimulatorPermissions
from .models import Simulator, SimulatorUser
from backend.helpers import SAFE_ACTIONS
from rest_framework.decorators import action
from rest_framework.response import Response
from pages.serializers import AdminPageSerializer
logger = logging.getLogger("django.server")


class AdminSimulatorViewSet(AdminApplicationViewSet):
    pagination_class = None
    serializer_class = AdminSimulatorSerializer
    permission_classes = [SimulatorPermissions]

    @action(detail=False, methods=["post"])
    def reorder(self, request, *args, **kwargs):
        if "ids" in request.data:
            if "group" in request.data:
                if not Simulator.objects.filter(group__id=request.data['group']).count() == len(request.data['ids']):
                    return  Response({'simulators': "Неверное количество симуляторов"}, status=status.HTTP_400_BAD_REQUEST)
            for idx, id in enumerate(request.data['ids']):
                try:
                    simulator = Simulator.objects.get(id=id)
                    if not simulator.is_user_owner(request.user):
                        return Response({'simulator': f"У вас нет права изменять симулятор с id = {id}"}, status=status.HTTP_400_BAD_REQUEST)
                    simulator.sequence_no = idx+1
                    simulator.save()
                except:
                    return  Response({'simulator': f"Симулятора с id {id} не существует"}, status=status.HTTP_400_BAD_REQUEST)
        return Response()

    @action(detail=True, methods=["get"])
    def onboarding(self, request, *args, **kwargs):
        return Response(AdminPageSerializer(self.get_object().onboarding).data)

    def get_queryset(self):
        queryset = Simulator.objects.all()
        if self.params.get('group') and not self.action in SAFE_ACTIONS:
            queryset = queryset.filter(group=self.params.get("group"))
        queryset = queryset.order_by("sequence_no")
        return queryset


class SimulatorViewSet(viewsets.GenericViewSet):
    pagination_class = None
    
    @action(detail=False, methods=['get'])
    def details(self, request, *args, **kwargs):
        if request.simulator:
            return Response(SimulatorSerializer(request.simulator).data)
        elif 'simulator' in request.query_params:
            simulator = get_object_or_404(Simulator, id=request.query_params.get('simulator'))
            return Response(SimulatorSerializer(simulator).data)
        return Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def page(self, request, *args, **kwargs):
        from pages.models import Page
        sim_user = SimulatorUser.objects.filter(user=request.user, simulator=request.simulator).first()
        if sim_user:
            if "page" in request.data:
                sim_user.current_page = Page.objects.get(id=request.data['page'])
            else:
                sim_user.current_page = None
            sim_user.save()
        return Response()