from rest_framework.permissions import IsAuthenticated
from rest_framework import mixins, permissions
from rest_framework import viewsets
from django.utils import timezone
from datetime import datetime

from utils.audit.views import LoggingMixin, ModelLoggingMixin


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and (request.user.is_superuser or request.method in permissions.SAFE_METHODS)


class AuthorizedViewSet(LoggingMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @property
    def params(self):
        return self.request.query_params

    @staticmethod
    def parsed_int(value):
        try:
            return int(value)
        except:
            return None

    @staticmethod
    def parsed_date(value):
        try:
            return timezone.make_aware(datetime.strptime(value, '%d.%m.%Y %H:%M:%S'))
        except:
            try:
                return timezone.make_aware(datetime.strptime(value, '%d.%m.%Y %H:%M'))
            except:
                try:
                    return timezone.make_aware(datetime.strptime(value, '%d.%m.%Y'))
                except:
                    return None


class AdminAuthorizedViewSet(AuthorizedViewSet):
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


class ReadOnlyViewSet(viewsets.ReadOnlyModelViewSet, AuthorizedViewSet):
    pass


class ApplicationReadOnlyViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, AuthorizedViewSet):
    pass


class ApplicationViewSet(ModelLoggingMixin, viewsets.ModelViewSet, AuthorizedViewSet):
    pass


class AdminApplicationViewSet(ModelLoggingMixin, viewsets.ModelViewSet, AdminAuthorizedViewSet):
    pass
