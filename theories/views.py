
from .permissions import TheoryChapterPermissions
from backend.application_viewset import AdminApplicationViewSet, ApplicationReadOnlyViewSet
from .serializers import TheoryChapterSerializer, AdminTheoryChapterSerializer
from .models import TheoryChapter
import logging

logger = logging.getLogger("django.server")
# Create your views here.


class AdminTheoryChapterViewSet(AdminApplicationViewSet):
    pagination_class = None
    serializer_class = AdminTheoryChapterSerializer
    permission_classes = [TheoryChapterPermissions]

    def get_queryset(self):
        
        if "simulator" in self.params:
            queryset = TheoryChapter.objects.filter(simulator__id=self.params.get('simulator'))
        else:
            queryset = TheoryChapter.objects.all()
        
        return queryset


class TheoryChapterViewSet(ApplicationReadOnlyViewSet):
    pagination_class = None
    serializer_class = TheoryChapterSerializer
    def get_queryset(self):
        if not self.request.user.is_anonymous:
            queryset = TheoryChapter.objects.filter(completed_by_user_set__in=[self.request.user])
        else:
            queryset = TheoryChapter.objects.all()

        return queryset
