from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response

from backend.application_viewset import AdminApplicationViewSet, ReadOnlyViewSet
from backend.helpers import SAFE_ACTIONS
from products.permissions import ProductPermissions
from .models import Product
from .serializers import AdminProductSerializer, ProductSerializer


class AdminProductsViewSet(AdminApplicationViewSet):
    serializer_class = AdminProductSerializer
    permission_classes = [ProductPermissions]

    def get_queryset(self):
        if self.params.get('simulator') and self.action not in SAFE_ACTIONS:
            queryset = Product.objects.filter(simulator__id=self.params.get('simulator'))
        else:
            queryset = Product.objects.all()
        return queryset


class ProductsViewSet(ReadOnlyViewSet):
    pagination_class = None
    serializer_class = ProductSerializer

    @action(detail=True, methods=['post'])
    def buy(self, request, *args, **kwargs):
        product = self.get_object()
        product.send_email(request.user, product.simulator.group.email_sender)

        product.users.add(request.user)

        request.user.balance -= product.cost
        request.user.save()

        return Response(status=status.HTTP_200_OK)

    def get_queryset(self):
        return Product.objects.filter(simulator=self.request.simulator)
