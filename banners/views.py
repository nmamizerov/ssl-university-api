from django.shortcuts import render
from django.db.models import Q
from backend.application_viewset import AdminApplicationViewSet, ReadOnlyViewSet
from backend.helpers import SAFE_ACTIONS
from .permissions import BannerPermissions
from .models import Banner
from .serializers import AdminBannerSerializer, BannerSerializer


class AdminBannersViewSet(AdminApplicationViewSet):
    pagination_class = None
    serializer_class = AdminBannerSerializer
    permission_classes = [BannerPermissions]

    def get_queryset(self):
        if self.params.get('group') and self.action not in SAFE_ACTIONS:
            queryset = Banner.objects.filter(group__id=self.params.get('group'))
        else:
            queryset = Banner.objects.all()
        return queryset


class BannersViewSet(ReadOnlyViewSet):
    serializer_class = BannerSerializer

    def get_queryset(self):
        if self.request.user.company is None:
            return Banner.objects.filter(company = None)
        else: 
            return Banner.objects.filter(company = self.request.user.company)
