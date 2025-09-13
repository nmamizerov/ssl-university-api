from backend.application_viewset import AdminApplicationViewSet
from backend.helpers import SAFE_ACTIONS
from .models import Email
from .serializers import AdminEmailSerializer


class AdminEmailViewSet(AdminApplicationViewSet):
    pagination_class = None
    serializer_class = AdminEmailSerializer

    def get_queryset(self):
        if self.params.get('simulator') and self.action not in SAFE_ACTIONS:
            queryset = Email.objects.filter(simulator__id=self.params.get('simulator'))
        elif self.params.get('group') and self.action not in SAFE_ACTIONS:
            queryset = Email.objects.filter(simulator__id=self.params.get('group'))
        else:
            queryset = Email.objects.all()
        return queryset
