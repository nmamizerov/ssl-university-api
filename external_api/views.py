import logging
from copy import deepcopy
import uuid

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.http import HttpResponse

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from datetime import timedelta, datetime, timezone

from external_api.serializers import ExternalUserSerializer
from simulators.models import Simulator, SimulatorUser
from subscriptions.models import UserSubscription
from user_profile.views import auth
User = get_user_model()
logger = logging.getLogger("django.server")


class ExternalAuthAttemptViewSet(viewsets.ModelViewSet):
    pagination_class = None

    @action(detail=False, methods=['post'], url_path='auto_registration')
    def auto_registration(self, request):
        try:
            authorized_user = auth(content=request.data, need_temporary_code=True)
        except Exception as error:
            return Response(error.args, status=status.HTTP_400_BAD_REQUEST)
        subscription = UserSubscription(user=authorized_user)
        subscription.valid_until = datetime.now(timezone.utc) + timedelta(days=75000)
        subscription.subscription_id = 16
        subscription.type = 6
        subscription.save()

        return Response({"code": authorized_user.temporary_code}, status=status.HTTP_200_OK)
        return HttpResponse(password)

    @action(detail=False, methods=['post'], url_path='api_registration')
    def api_registration(self, request):
        try:
            authorized_user = auth(content=request.data, need_temporary_code=True)
        except Exception as error:
            return Response(error.args, status=status.HTTP_400_BAD_REQUEST)

        return Response(authorized_user.temporary_code)

    @action(detail=False, methods=['post'], url_path='api_login')
    def api_login(self, request):
        try:
            authorized_user = auth(content=request.data, is_auto_login=True, need_temporary_code=True)
        except Exception as error:
            return Response(error.args, status=status.HTTP_400_BAD_REQUEST)

        return Response(authorized_user.temporary_code)

    @action(detail=False, methods=['post'], url_path='default_auth')
    def default_auth(self, request):
        try:
            content = {
                'email': '{}@default.com'.format(uuid.uuid4().hex[:16]),
                'first_name': 'игрока',
                'last_name': 'Персонаж',
                'male': True,
                'group': request.data['group']
            }
            authorized_user = auth(content=content, need_temporary_code=True)
        except Exception as error:
            return Response({'detail': str(error)}, status=status.HTTP_400_BAD_REQUEST)

        subscription = UserSubscription(user=authorized_user)
        subscription.save()

        return Response({"code": authorized_user.temporary_code}, status=status.HTTP_200_OK)


class ExternalSimulatorsViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = Simulator.objects.all()
    lookup_field = 'token'

    @action(detail=True, methods=['post'], url_path='set_paid')
    def set_paid(self, request, *args, **kwargs):
        simulator = self.get_object()

        if 'user_id' in request.data:
            simulator_user = get_object_or_404(SimulatorUser, simulator=simulator, user__id=request.data['user_id'])
        elif 'user_email' in request.data:
            simulator_user = get_object_or_404(SimulatorUser, simulator=simulator, user__email=request.data['user_email'])
        else:
            return Response({
                "user": "В запросе отсутствует необходимое поле (user_id или user_email)!"
            }, status=status.HTTP_400_BAD_REQUEST)

        if 'set_paid' in request.data:
            try:
                simulator_user.simulator_paid = request.data['set_paid']
                simulator_user.save()
            except Exception as exception:
                logger.exception(exception)
                return Response({'set_paid': "Неверный формат, должен быть тип boolean!"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'set_paid': "В запросе отсутствует необходимое поле!"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"is_paid": simulator_user.simulator_paid}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='update_user')
    def update_user(self, request, *args, **kwargs):
        simulator = self.get_object()
        if 'user_id' in request.data:
            user = get_object_or_404(SimulatorUser, simulator=simulator, user__id=request.data['user_id']).user
        elif 'user_email' in request.data:
            user = get_object_or_404(SimulatorUser, simulator=simulator, user__email=request.data['user_email']).user
        else:
            return Response({
                "user": "В запросе отсутствует необходимое поле (user_id или user_email)!"
            }, status=status.HTTP_400_BAD_REQUEST)

        data = deepcopy(request.data)
        data['id'] = user.id
        user.avatar = request.FILES.get('avatar')
        user.save()

        serializer = ExternalUserSerializer(data=data, context=request)
        if serializer.is_valid():
            serializer.update(instance=user, validated_data=serializer.data)
            return Response(status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

