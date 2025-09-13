from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from backend.application_viewset import AdminApplicationViewSet, ReadOnlyViewSet
from backend.helpers import SAFE_ACTIONS
from .permissions import SubscriptionPermissions
from .models import Subscription, UserSubscription
from .serializers import AdminSubscriptionSerializer, SubscriptionSerializer


class AdminSubscriptionViewSet(AdminApplicationViewSet):
    pagination_class = None
    serializer_class = AdminSubscriptionSerializer
    permission_classes = [SubscriptionPermissions]

    def get_queryset(self):
        if self.params.get('group') and self.action not in SAFE_ACTIONS:
            queryset = Subscription.objects.filter(group__id=self.params.get('group'))
        else:
            queryset = Subscription.objects.all()
        return queryset


class SubscriptionViewSet(ReadOnlyViewSet):
    serializer_class = SubscriptionSerializer
    pagination_class = None

    def get_queryset(self):
        if 'group' in self.params:
            return Subscription.objects.filter(group__id=self.params.get('group'))
        return Subscription.objects.all()

    @action(detail=True, methods=['post'])
    def pay(self, request, *args, **kwargs):
        subscription = self.get_object()
        user_subscription = get_object_or_404(UserSubscription, user=request.user)

        user_subscription.subscription = subscription
        user_subscription.save()

        try:
            payload = user_subscription.pay(period=request.data['period'])
            return Response(payload, status=status.HTTP_200_OK)
        except ValueError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def change_subscribe(self, request, *args, **kwargs):
        user_subscription = get_object_or_404(UserSubscription, user=request.user)

        if user_subscription.type >= 5:
            user_subscription.resubscribe = not user_subscription.resubscribe
            user_subscription.save()
        else:
            return Response({'detail': "У вас нет подписки"}, status=status.HTTP_400_BAD_REQUEST)

        if user_subscription.resubscribe:
            user_subscription.subscription.send_email(5, user_subscription.user)
        else:
            user_subscription.subscription.send_email(4, user_subscription.user)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def send_mailing_list(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        subscribers = UserSubscription.objects.filter(type__gte=5)
        for subscriber in subscribers:
            subscriber.subscription.send_email(7, subscriber.user)

        return Response(status=status.HTTP_204_NO_CONTENT)
