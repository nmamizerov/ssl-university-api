from django.db.models.deletion import CASCADE
from pages.models import Page
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth import get_user_model
from django.conf import settings
import requests
from simulators.models import SimulatorUser
from theories.models import TheoryChapter
from characters.models import Character
from django.db.models import Q
import logging
import re
logger = logging.getLogger("django.server")
# logging.basicConfig(filename='example.log', level=logging.DEBUG)
User = get_user_model()
import json

PLACE_TYPE_CHOICES = [
    ('theory', 'Теория'),
    ('question', 'Вопрос'),
    ('message', 'Сообщение'),
    ('safetext', 'Текст'),
    ('openquestion', 'Открытый вопрос'),
    ('test', 'Тест'),
    ('openquestionexpert', 'Открытый вопрос эксперту'),
    ('questionanswercheck', 'Открытый вопрос с проверкой'),
    ('questionuserchoice', 'Вопрос с выбором пользователя'),
    ('questionrange', 'Открытый вопрос с проверкой значения на интервале'),
    ('questionexternal', 'Внешний вопрос'),
    ('aiopenquestion', 'Вопрос с нейронками'),
    ('testaiopenquestion', 'Тестовый вопрос с нейронками'),
]


class PlaceExpertException(ValueError):
    __message = 'Запрос на комментарий эксперта успешно отправлен! Ожидайте проверки...'

    def __init__(self):
        super().__init__(self.__message)


# Create your models here.
class Place(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    type = models.CharField(choices=PLACE_TYPE_CHOICES, max_length=200)
    text = models.TextField(blank=True, null=True)
    title = models.CharField(max_length=10000, blank=True, null=True)
    female_text = models.TextField(blank=True, null=True, )
    text_description = models.TextField(null=True, blank=True)
    postreply_text = models.TextField(blank=True, null=True, )
    postreply_female_text = models.TextField(blank=True, null=True)
    postreply_error_text = models.TextField(blank=True, null=True)
    postreply_error_female_text = models.TextField(blank=True, null=True)
    comment_number = models.IntegerField(blank=True, null=True)
    is_start = models.BooleanField(default=False)
    is_end = models.BooleanField(default=False)
    points = models.IntegerField(default=0, null=True, blank=True)
    points_error = models.IntegerField(default=0, null=True, blank=True)
    comment_advice = models.TextField(blank=True, null=True, )
    comment_female_advice = models.TextField(blank=True, null=True, )
    correct_answer = models.TextField(blank=True, null=True, )

    script_id = models.CharField(max_length=300, blank=True, null=True)
    script_text = models.TextField(blank=True, null=True)
    need_notifications = models.BooleanField(blank=True, null=True)
    award = models.IntegerField(blank=True, null=True)
    award_error = models.IntegerField(blank=True, null=True)
    theory_chapter = models.ForeignKey(TheoryChapter, blank=True, null=True, on_delete=models.PROTECT)
    character = models.ForeignKey(Character, blank=True, null=True, on_delete=models.PROTECT)
    node_position_x = models.IntegerField(blank=True, null=True)
    node_position_y = models.IntegerField(blank=True, null=True)
    node_id = models.CharField(max_length=300, blank=True, null=True)
    node_info = JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)
    answers = JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)
    parent_message = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    next_places = JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)
    is_multiple = models.BooleanField(null=True, blank=True)
    forced_role = models.CharField(max_length=255, blank=True, null=True)
    is_hero = models.BooleanField(default=False)
    is_current_user = models.BooleanField(default=False)
    is_author_message = models.BooleanField(default=False)
    block_complete = models.BooleanField(default=False)
    auto_answers = models.JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)
    auto_answer = models.CharField(max_length=500, blank=True, null=True)
    need_user = models.BooleanField(default=False)
    need_payment = models.BooleanField(default=False)
    gpt_generate = models.BooleanField(default=False)
    preprompt = models.TextField(null=True, blank=True)
    request_id = models.IntegerField(blank=True, null=True)

    def get_answer_to_comment(self, user):
        answer_to_comment = PlaceUser.objects.filter(~Q(answers=None) & ~Q(user=user) & ~Q(commented_by_user_set=user), is_completed=True, place=self).order_by("commented_count").first()
        if answer_to_comment:
            if answer_to_comment.user.avatar:
                character = {
                    "first_name": answer_to_comment.user.first_name,
                    "last_name": answer_to_comment.user.last_name,
                    "avatar": answer_to_comment.user.avatar.url
                }
            else:
                character = {
                    "first_name": answer_to_comment.user.first_name,
                    "last_name": answer_to_comment.user.last_name,
                    "avatar": None
                }
            answer_to_comment.commented_by_user_set.add(user)
            answer_to_comment.commented_count = answer_to_comment.commented_count + 1
            answer_to_comment.save()
            return {
                "id": answer_to_comment.id,
                'text': answer_to_comment.answers,
                "character": character,
                "commented": False,
                "comment": None
            }
        return None

    def get_next_place(self, user, p_user):
        place_user = PlaceUser.objects.get(user=user, place=self)
        if self.type == 'openquestion' and self.comment_number:
            if not place_user.commented_answers or len(place_user.commented_answers) < self.comment_number:
                if not place_user.commented_answers:
                    place_user.commented_answers = []
                if len(place_user.commented_answers) < self.comment_number:
                    answer_to_comment = self.get_answer_to_comment(place_user.user)
                    if answer_to_comment:
                        place_user.commented_answers.append(answer_to_comment)
                        for idx, place in enumerate(p_user.places):
                            if place['id'] == self.id:
                                if not 'commented_answers' in place:
                                    p_user.places[idx]['commented_answers'] = []
                                p_user.places[idx]['commented_answers'].append(answer_to_comment)
                        p_user.save()
                        place_user.save()
                        return self
                    else:
                        place_user.is_completed = True
                        for idx, place in enumerate(p_user.places):
                            if place['id'] == self.id:
                                p_user.places[idx]['complete'] = True
                                p_user.save()
                        place_user.save()

        points = place_user.points
        if not self.next_places:
            return None
        if not 'places' in self.next_places:
            return None
        next_place = None
        next_places = [place for place in self.next_places['places'] if 'award' in place]
        next_places = sorted(next_places, key=lambda k: int(k['award']), reverse=True)
        for place in next_places:
            if points >= int(place['award']):
                next_place = Place.objects.filter(id=place['place']).first()
                if not next_place:
                    continue
                break
        return next_place

    def finish_complete(self, user, simulator, page_user):
        from places.serializers import PlaceUserInfoSerializer

        next_place_data = None
        next_page_data = None
        next_lesson_data = None

        next_place = self.get_next_place(user, page_user)
        if next_place:
            if not next_place.id == self.id:
                next_place_data = PlaceUserInfoSerializer(next_place).data
                if next_place.type == 'message':
                    if next_place.gpt_generate:
                        user_answer = ''
                        for idx, place in enumerate(page_user.places):
                            if next_place.parent_message.id == int(place['id']):
                                user_answer = place['user_answer']
                        if user_answer:
                            text = next_place.preprompt.replace("%phrase%", user_answer)
                            user_answer = next_place.aiservice(text)
                            next_place_data['text'] = user_answer
                page_user.places.append(next_place_data)
                page_user.save()
        else:
            page_user.completed = True
            if page_user.page.is_onboarding_for:
                sim_user = SimulatorUser.objects.get(simulator=simulator, user=user)
                sim_user.onboarding_complete = True
                sim_user.save()
            next_page_data = page_user.page.get_next_page(page_user, user)
            page_user.save()
            if not next_page_data:
                if page_user.page.lesson:
                    next_lesson_data = page_user.page.lesson.get_next_lesson(user)
                    if not next_lesson_data:
                        page_user.page.lesson.simulator.complete(user)

        return next_place_data, next_page_data, next_lesson_data

    def complete_place(self, user, p_user, points=0, award=0, *args, **kwargs):
        if not award:
            award = 0
        user.write_history(value=award, lesson=self.page.lesson)

        if not points:
            points = 0

        place_user = PlaceUser.objects.filter(user=user, place=self).first()
        answers = None
        user_answer = None
        is_correct = None
        if not place_user:
            place_user = PlaceUser(user=user, place=self)

        if 'answers' in kwargs:
            if 'is_correct' in kwargs:
                is_correct = kwargs['is_correct']
            answers = kwargs['answers']
            place_user.answers = answers

        if 'user_answer' in kwargs:
            if 'is_correct' in kwargs:
                is_correct = kwargs['is_correct']
            user_answer = kwargs['user_answer']
            place_user.answers = user_answer

        place_user.points = points
        if self.type == 'openquestion' and self.comment_number:
            if not (not place_user.commented_answers or not len(place_user.commented_answers) >= self.comment_number):
                place_user.is_completed = True
        else:
            place_user.is_completed = True

        for idx, place in enumerate(p_user.places):
            if self.id == int(place['id']):
                if self.type == 'openquestion' and self.comment_number:
                    if not (not place_user.commented_answers or not len(
                            place_user.commented_answers) >= self.comment_number):
                        p_user.places[idx]['complete'] = True
                else:
                    p_user.places[idx]['complete'] = True
                p_user.places[idx]['user_answers'] = answers
                p_user.places[idx]['user_answer'] = user_answer
                p_user.places[idx]['is_correct'] = is_correct
        p_user.points += points
        p_user.save()
        place_user.save()

    def theory_action(self, user, p_user, *args, **kwargs):
        if self.theory_chapter:
            self.theory_chapter.completed_by_user_set.add(p_user.user)
            self.save()
        self.complete_place(user, p_user, points=self.points, award=self.award)

    def question_action(self, user, p_user, *args, **kwargs):
        points = 0
        award = 0
        is_correct = True

        answers = kwargs['answers']
        if self.is_multiple: 
            right_answers = 0
            for answer_base in self.answers:
                if answer_base['is_correct']:
                    right_answers+=1
            if len(answers) < right_answers:
                is_correct = False
        for idx, answer in enumerate(self.answers):
            if idx not in answers:
                continue

            if not answer['is_correct']:
                is_correct = False

            if 'points' in answer and bool(re.sub("[^0-9]", "", str(answer['points']))):
                points += int(re.sub("[^0-9]", "", str(answer['points'])))
            if 'award' in answer and bool(re.sub("[^0-9]", "", str(answer['award']))):
                award += int(re.sub("[^0-9]", "", str(answer['award'])))

        if is_correct:
            if self.points:
                points += self.points
            if self.award:
                award += self.award
        else:
            if self.points_error:
                points += self.points_error
            if self.award_error:
                award += self.award_error

        self.complete_place(user, p_user, points=points, award=award, answers=answers, is_correct=is_correct)

    def message_action(self, user, p_user, *args, **kwargs):
        self.complete_place(user, p_user, points=self.points, award=self.award)

    def safetext_action(self, user, p_user, *args, **kwargs):
        self.complete_place(user, p_user, points=self.points, award=self.award)

    def openquestion_action(self, user, p_user, *args, **kwargs):
        self.complete_place(user, p_user, user_answer=kwargs['user_answer'], award=self.award)

    def aiopenquestion_action(self, user, p_user, *args, **kwargs):
        val = self.aiservice(kwargs['user_answer'])
        self.auto_answer = val
        flag = False
        if self.auto_answers:
            for answer in self.auto_answers:
                if answer['value'] == val:
                    self.points = int(answer['points'])
                    flag = True
        if not flag: 
            for link in self.next_places['places']:
                if str(val) == str(link['award']): 
                    flag=True
                    self.points = int(link['award'])
        if not flag: 
            self.points = -1
        self.save()
        self.complete_place(user, p_user, user_answer=kwargs['user_answer'], points=self.points)
    
    def testaiopenquestion_action(self, user, p_user, *args, **kwargs):
        val = self.aiservicetest(kwargs['user_answer'], user.username)
        self.auto_answer = val
        flag = False
        if self.auto_answers:
            for answer in self.auto_answers:
                if answer['value'] == val:
                    self.points = int(answer['points'])
                    flag = True
        if not flag: 
            for link in self.next_places['places']:
                if val == link['award']: 
                    flag=True
                    self.points = int(link['award'])
        if not flag: 
            self.points = -1
        self.save()
        self.complete_place(user, p_user, user_answer=kwargs['user_answer'], points=self.points)

    def openquestionexpert_action(self, user, p_user, *args, **kwargs):
        from comment_requests.models import CommentRequest
        comment_request = CommentRequest(place=self, user=user)
        comment_request.save()

        if self.block_complete:
            place_user = PlaceUser(user=user, place=self)
            user_answer = kwargs['user_answer']
            place_user.answers = user_answer
            place_user.save()

            for idx, place in enumerate(p_user.places):
                if self.id == int(place['id']):
                    p_user.places[idx]['user_answer'] = user_answer

            p_user.save()

            raise PlaceExpertException()

        self.complete_place(user, p_user, user_answer=kwargs['user_answer'], award=self.award)

    def questionrange_action(self, user, p_user, *args, **kwargs):
        points = 0
        if self.points:
            points = self.points

        award = 0
        if self.award:
            award = self.award

        answer = int(self.correct_answer)
        answer_min = int(kwargs['user_answer_min'])
        answer_max = int(kwargs['user_answer_max'])

        is_correct = True
        if answer < answer_min or answer > answer_max:
            is_correct = False
            if self.points_error is not None:
                points = self.points_error
            if self.award_error is not None:
                award = self.award_error

        self.complete_place(user, p_user, user_answer="{} - {}".format(answer_min, answer_max), points=points, award=award, is_correct=is_correct)

    def questionanswercheck_action(self, user, p_user, *args, **kwargs):
        points = 0
        if self.points:
            points = self.points

        award = 0
        if self.award:
            award = self.award

        answer = kwargs['user_answer'].strip().lower()

        is_correct = True
        if not answer == self.correct_answer.strip().lower():
            is_correct = False
            if self.points_error is not None:
                points = self.points_error
            if self.award_error is not None:
                award = self.award_error

        self.complete_place(user, p_user, user_answer=kwargs['user_answer'], points=points, award=award, is_correct=is_correct)

    def questionuserchoice_action(self, user, p_user, *args, **kwargs):
        points = 0
        award = 0

        u_answer = kwargs['answers']
        for idx, answer in enumerate(self.answers):
            if idx == u_answer:
                if 'points' in answer and  bool(re.sub("[^0-9]", "", answer['points'])):
                    points += int(re.sub("[^0-9]", "", answer['points']))
                if 'award' in answer and bool(re.sub("[^0-9]", "", answer['award'])):
                    award += int(re.sub("[^0-9]", "", answer['award']))

        if self.points:
            points += self.points
        if self.award:
            award += self.award

        self.complete_place(user, p_user, points=points, award=award, answers=u_answer)

    def questionexternal_action(self, user, p_user, *args, **kwargs):
        self.complete_place(user, p_user, points=self.points, award=self.award)


    def aiservice(self, text):
        ai_endpoint_url = settings.AI_ENDPOINT_URL
        data = {
            "value": text, 
            "request": self.request_id
        }
        headers = {'Authorization': 'Bearer ' + 'EeFpTyQH2ReuGUV6A3lLtlVxUN4LrHhY', "Content-Type": "application/json"}
        jsonStr = json.dumps(data)
        response = requests.post(ai_endpoint_url, headers = headers, data=jsonStr)
        return response.json()['response']
    
    def aiservicetest(self, text, email):
        ai_endpoint_url = settings.AI_TEST_ENDPOINT_URL
        data = {
            "value": text, 
            "training_step": self.request_id,
            "email": email
        }
        headers = {'Authorization': 'Bearer ' + 'EeFpTyQH2ReuGUV6A3lLtlVxUN4LrHhY', "Content-Type": "application/json"}
        jsonStr = json.dumps(data)
        response = requests.post(ai_endpoint_url, headers = headers, data=jsonStr)
        return response.json()['response']

    def __str__(self):
        return '(id={}){} - {}'.format(self.id, self.type, self.text)


class PlaceUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    admin_comment_requested = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    answers = JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)
    comments = JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)
    commented_answers = JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)
    commented_by_user_set = models.ManyToManyField(User, blank=True, related_name='commented_answers')
    commented_count = models.IntegerField(default=0)

    def __str__(self):
        return '{} - {}'.format(self.place, self.user)
