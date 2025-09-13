import json

from backend.application_pagination import ApplicationPagination
from lessons.permissions import LessonPermissions
from backend.application_viewset import AdminApplicationViewSet, ApplicationReadOnlyViewSet, ApplicationViewSet
from places.models import PlaceUser
from places.serializers import PlaceUserSerializer
from recommendations.models import Recommendation
from tags.models import Tag
from .serializers import LessonSerializer, AdminLessonSerializer
from .permissions import LessonPermissions
from .models import Lesson, UserLessonProgress
from pages.models import Page
from backend.helpers import SAFE_ACTIONS
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
import logging, math
# logging.basicConfig(filename='example.log', level=logging.DEBUG)


logger = logging.getLogger("django.server")


class AdminLessonViewSet(AdminApplicationViewSet):
    pagination_class = None
    serializer_class = AdminLessonSerializer
    permission_classes = [LessonPermissions]

    def update(self, request, *args, **kwargs):
        lesson = self.get_object()
        lesson.tag_set.clear()
        if 'tags' in request.data:
            tags = request.data['tags']
            for tag_id in tags:
                tag = Tag.objects.get(id=tag_id)
                lesson.tag_set.add(tag)

        lesson.recommendation_set.clear()
        if 'recommendations' in request.data and len(request.data['recommendations'])>0:
            recommendations = request.POST.getlist('recommendations')
            for recommendation_id in recommendations:
                recommendation = Recommendation.objects.get(id=recommendation_id)
                lesson.recommendation_set.add(recommendation)

        return super(AdminLessonViewSet, self).update(request, *args, **kwargs)

    @action(detail=False, methods=["post"])
    def reorder(self, request, *args, **kwargs):
        if "ids" in request.data:
            if "simulator" in request.data:
                if not Lesson.objects.filter(simulator__id=request.data['simulator']).count() == len(request.data['ids']):
                    return Response({'lessons': "Неверное количество уроков"}, status=status.HTTP_400_BAD_REQUEST)
            for idx, id in enumerate(request.data['ids']):
                try:
                    lesson = Lesson.objects.get(id=id)
                    if not lesson.is_user_owner(request.user):
                        return Response({'lesson': f"У вас нет права изменять урок с id = {id}"}, status=status.HTTP_400_BAD_REQUEST)
                    lesson.sequence_no = idx+1
                    lesson.save()
                except:
                    return Response({'lesson': f"Урока с id {id} не существует"}, status=status.HTTP_400_BAD_REQUEST)
        return Response()

    @action(detail=True, methods=["get"])
    def lesson_statistics_amount(self, request, *args, **kwargs):
        lesson = self.get_object()
        users_progress = UserLessonProgress.objects.filter(lesson=lesson)
        return Response(int(math.ceil(len(users_progress) / 100)))

    @action(detail=True, methods=["get"])
    def lesson_statistics(self, request, *args, **kwargs):
        lesson = self.get_object()
        users_progress = UserLessonProgress.objects.filter(lesson=lesson)

        paginator = ApplicationPagination()
        page = paginator.paginate_queryset(users_progress, request)

        places = PlaceUser.objects.filter(place__page__lesson=lesson, user__in=[user.user for user in page])

        return Response({
            'places': PlaceUserSerializer(instance=places, many=True, context=request).data,
            'lesson': lesson.name
        })

    def get_queryset(self):
        queryset = []
        if self.params.get('simulator') and self.action not in SAFE_ACTIONS:
            queryset = Lesson.objects.filter(simulator__id=self.params.get('simulator'))
        elif self.params.get('group') and self.action not in SAFE_ACTIONS:
            queryset = Lesson.objects.filter(simulator__group__id=self.params.get('group'))
        else:
            queryset = Lesson.objects.all()
        queryset = queryset.order_by("sequence_no")
        return queryset


class LessonViewSet(ApplicationViewSet):
    def get_serializer_class(self):
        if self.action == 'list':
            return LessonSerializer
        return LessonSerializer

    def get_queryset(self):
        queryset = Lesson.objects.all()
        if self.action == "set_first_uncompleted_page":
            return queryset
        if self.request.simulator:
            queryset = queryset.filter(simulator=self.request.simulator)
        if 'simulator' in self.params:
            queryset = queryset.filter(simulator__id=self.params.get('simulator'))
        if 'tag' in self.params:
            if self.params.get('tag') == 'all':
                queryset = queryset.exclude(tag__isnull=True)
            elif self.params.get('tag') == 'all_wn':
                queryset = queryset
            else:
                queryset = queryset.filter(tag__id=self.params.get('tag'))
        if 'group' in self.params:
            queryset = queryset.filter(simulator__group__id=self.params.get('group'))

        return queryset.exclude(active=False).order_by("sequence_no")

    @action(detail=False, methods=['get'])
    def lesson(self, request, *args, **kwargs):
        lesson = get_object_or_404(Lesson, slug=self.params.get('slug'))
        return Response(LessonSerializer(instance=lesson, context={'request': request}).data)

    @action(detail=True, methods=["post"])
    def start(self, request, *args, **kwargs):
        is_started = self.get_object().start(request.user)
        if is_started:
            return Response()
        return Response({"page": "У урока нет начальной страницы"}, status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def set_first_uncompleted_page(self, request, *args, **kwargs):
        lesson = self.get_object()
        lesson_progress = UserLessonProgress.objects.get(lesson=lesson, user=request.user)
        lesson_progress.first_uncompleted_page = get_object_or_404(Page, pk=request.data['page'])
        lesson_progress.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
