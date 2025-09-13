
from backend.application_viewset import AdminApplicationViewSet
from .serializers import CharacterSerializer
from .models import Character
from .permissions import CharacterPermissions
import logging

logger = logging.getLogger("django.server")
# Create your views here.


class AdminCharacterViewSet(AdminApplicationViewSet):
    pagination_class = None
    serializer_class = CharacterSerializer
    permission_classes = [CharacterPermissions]

    def get_queryset(self):
        if "simulator" in self.params:
            queryset = Character.objects.filter(simulator__id=self.params.get('simulator'))
        else:
            queryset = Character.objects.all()
        return queryset