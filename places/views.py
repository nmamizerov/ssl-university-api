import logging
from simulators.models import SimulatorUser, Simulator
from django.shortcuts import render, get_object_or_404
from rest_framework import permissions
from backend.application_viewset import AdminApplicationViewSet, ApplicationReadOnlyViewSet
from .serializers import PlaceSerializer, PlaceUserInfoSerializer
from .models import Place, PlaceUser, PlaceExpertException
from pages.models import UserPageProgress
from backend.helpers import SAFE_ACTIONS
from .permissions import PlacePermissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from notifications.models import Notification
from bot.models import tgUser, tgSend
# logging.basicConfig(filename='example.log', level=logging.DEBUG)
import re


class AdminPlaceViewSet(AdminApplicationViewSet):
    pagination_class = None
    serializer_class = PlaceSerializer
    permission_classes = [PlacePermissions]

    def perform_destroy(self, instance):
        instance.page.delete_place(instance.id)
        instance.delete()

    def get_queryset(self):
        queryset = []
        if self.params.get('page') and not self.action in SAFE_ACTIONS:
            queryset = Place.objects.filter(page__id=self.params.get('page'))
        elif self.params.get('lesson') and not self.action in SAFE_ACTIONS:
            queryset = Place.objects.filter(page__lesson__id=self.params.get('lesson'))
        else:
            queryset = Place.objects.all()
        return queryset


# добавить сериалайзер для пользовательского плейса
class PlaceViewSet(ApplicationReadOnlyViewSet):
    pagination_class = None
    serializer_class = PlaceSerializer
    queryset = Place.objects.all()

    @action(detail=False, methods=['post'])
    def comment(self, request, *args, **kwargs):
        if not 'place' in request.data or not 'comment' in request.data or not 'answer_id' in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        place = Place.objects.get(id=request.data['place'])
        p_user = PlaceUser.objects.filter(user=request.user, place=place).first()
        page_user = UserPageProgress.objects.get(page=place.page, user=request.user)
        page_user_place_idx = 0
        if not p_user:
            return Response(status=status.HTTP_404_NOT_FOUND)
        for idx, commented_answer in enumerate(p_user.commented_answers):
            if commented_answer['id'] == request.data['answer_id']:
                p_user.commented_answers[idx]['comment'] = request.data['comment']
                p_user.commented_answers[idx]['commented'] = True
        for idx_p, p_place in enumerate(page_user.places):
            if p_place['id'] == place.id:
                for idx_cp, commented_answer in enumerate(p_place['commented_answers']):
                    if commented_answer['id'] == request.data['answer_id']:
                        page_user_place_idx = idx_p
                        page_user.places[idx_p]['commented_answers'][idx_cp]['comment'] = request.data['comment']
                        page_user.places[idx_p]['commented_answers'][idx_cp]['commented'] = True
        commented_place = PlaceUser.objects.filter(id=request.data['answer_id']).first()

        notification = Notification(from_user=request.user,
                                    to_user=commented_place.user,
                                    answer=commented_place,
                                    text=request.data['comment'],
                                    type='user_comment')
        notification.save()
        tg_user = tgUser.objects.filter(user=commented_place.user).first()
        if tg_user is not None and tg_user.active: 
            TAG_RE = re.compile(r'<[^>]+>')
            question_text = TAG_RE.sub('', commented_place.place.text)
            
            message = f"""Вы получили комментарий на ваш ответ к вопросу: 
<b>{question_text}</b>


<i>{request.data['comment']}</i>

<a href=\"https://skillslab.center/blogs/{commented_place.place.page.lesson.slug}\">Перейти к уроку</a>"""
            tgSend.objects.create(
                tg=tg_user,
                message=message
            )

        if place.comment_number > len(p_user.commented_answers):
            answer_to_comment = place.get_answer_to_comment(request.user)
            if not answer_to_comment:
                page_user.places[page_user_place_idx]['complete'] = True
                p_user.is_completed = True
                request.data['user_answer'] = p_user.answers
                page_user.save()
                p_user.save()
                return self.complete_place(place, request)
            p_user.commented_answers.append(answer_to_comment)
            page_user.places[page_user_place_idx]['commented_answers'].append(answer_to_comment)
        else:
            page_user.places[page_user_place_idx]['complete'] = True
            p_user.is_completed = True
            request.data['user_answer'] = p_user.answers
            page_user.save()
            p_user.save()
            return self.complete_place(place, request)
        page_user.save()
        p_user.save()
        return Response()

    @action(detail=True, methods=["post"])
    def complete(self, request, *args, **kwargs):
        place = self.get_object()
        return self.complete_place(place, request)

    def complete_place(self, place, request):
        simulator = place.page.lesson.simulator
        page_user = UserPageProgress.objects.get(page=place.page, user=request.user)

        try:
            place_action = getattr(Place, f"{place.type}_action")
        except AttributeError:
            raise NotImplementedError("Class `{}` does not implement `{}`".format(Place.__class__.__name__, place.type))

        try:
            if place.type in ('question', 'questionuserchoice'):
                place_action(place, request.user, page_user, answers=request.data['answers'])
            elif place.type in ('openquestion', 'openquestionexpert', 'questionanswercheck'):
                place_action(place, request.user, page_user, user_answer=request.data['user_answer'])
            elif place.type in ('aiopenquestion', 'testaiopenquestion'):
                place_action(place, request.user, page_user, user_answer=request.data['user_answer'])
            elif place.type == 'questionrange':
                place_action(place, request.user, page_user, user_answer_min=request.data['user_answer_min'], user_answer_max=request.data['user_answer_max'])
            else:
                place_action(place, request.user, page_user)
        except PlaceExpertException:
            return Response(status=status.HTTP_204_NO_CONTENT)

        next_place_data, next_page_data, next_lesson_data = place.finish_complete(request.user, simulator, page_user)
        return Response({"place": next_place_data, "page": next_page_data, "lesson": next_lesson_data})
