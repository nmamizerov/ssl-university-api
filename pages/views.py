
from backend.application_viewset import AdminApplicationViewSet, ApplicationReadOnlyViewSet
from .serializers import AdminPageSerializer, PageSerializer
from .models import Page, UserPageProgress
from backend.helpers import SAFE_ACTIONS
from .permissions import PagePermissions
import logging
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger("django.server")
# Create your views here.


class AdminPageViewSet(AdminApplicationViewSet):
    pagination_class = None
    serializer_class = AdminPageSerializer
    permission_classes = [PagePermissions]

    @action(detail=False, methods=["post"])
    def reorder(self, request, *args, **kwargs):
        if "ids" in request.data:
            if "lesson" in request.data:
                if not Page.objects.filter(lesson__id=request.data['lesson']).count() == len(request.data['ids']):
                    return  Response({'pages': "Неверное количество страниц"}, status=status.HTTP_400_BAD_REQUEST)
            for idx, id in enumerate(request.data['ids']):
                try:
                    page = Page.objects.get(id=id)
                    if not page.is_user_owner(request.user):
                        return Response({'page': f"У вас нет права изменять страницу с id = {id}"}, status=status.HTTP_400_BAD_REQUEST)
                    page.sequence_no = idx+1
                    page.save()
                except:
                    return  Response({'page': f"Страницы с id {id} не существует"}, status=status.HTTP_400_BAD_REQUEST)
        return Response()

    def get_queryset(self):
        queryset = []
        if self.params.get('lesson') and not self.action in SAFE_ACTIONS:
            queryset = Page.objects.filter(lesson__id=self.params.get('lesson'))
        else:
            queryset = Page.objects.all()
        queryset = queryset.order_by("sequence_no")
        return queryset


class PageViewSet(ApplicationReadOnlyViewSet):
    pagination_class = None
    serializer_class = PageSerializer
    queryset = Page.objects.all()

    @action(detail=True, methods=["PATCH", 'PUT'])
    def score(self, request, *args, **kwargs):
        user_page = UserPageProgress.objects.filter(user=request.user, page=self.get_object()).first()
        user_page.utility = request.data['utility']
        user_page.fun = request.data['fun']
        user_page.save()
        return Response()
