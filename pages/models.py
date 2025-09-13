from django.db import models
from lessons.models import Lesson, UserLessonProgress
from simulators.models import Simulator
from user_profile.models import User
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Max

import logging
logger = logging.getLogger("django.server")

# Create your models here.
class Page(models.Model):
    name = models.CharField(max_length=200)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, blank=True, related_name='pages')
    completed_by_user_set = models.ManyToManyField(User, blank=True, related_name='completed_pages')
    sequence_no = models.PositiveIntegerField(null=True)
    is_onboarding_for = models.OneToOneField(Simulator, null=True, blank=True, on_delete=models.CASCADE, related_name='onboarding')
    is_test = models.BooleanField(default=False)
    is_start = models.BooleanField(default=False)
    is_end = models.BooleanField(default=False)
    need_answers = models.PositiveIntegerField(null=True, blank=True)
    page_after_test = models.ForeignKey('Page', on_delete=models.CASCADE, null=True, blank=True)
    is_page_after_test = models.BooleanField(default=False)
    places = JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)
    next_pages = JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)
    links = JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)

    @property
    def max_seq_no(self):
        seq_no = Page.objects.filter(lesson=self.lesson).aggregate(Max("sequence_no"))['sequence_no__max']
        if seq_no:
            seq_no = seq_no + 1
        else:
            seq_no = 1
        return seq_no

    def is_user_owner(self, user):
        return self.lesson.simulator.group.owner == user

    def append_place(self, place):
        from places.serializers import PlaceJsonInfoSerializer
        if not self.places:
            self.places = {
                "places": []
            }
        self.places['places'].append(PlaceJsonInfoSerializer(place).data)
        self.save()

    def delete_place(self, place_id):
        for idx, place in enumerate(self.places['places']):
            if place['id'] == place_id:
                self.places['places'].pop(idx)
        self.save()
    
    def update_place(self, place):
        from places.serializers import PlaceJsonInfoSerializer
        for idx, js_place in enumerate(self.places['places']):
            if js_place['id'] == place.id:
                self.places['places'][idx] = PlaceJsonInfoSerializer(place).data
        self.save()

    def get_user_progress(self, user):
        from places.models import Place
        from places.serializers import PlaceUserInfoSerializer
        from .serializers import UserPageProgressSerializer

        user_progress = UserPageProgress.objects.filter(user=user, page=self).first()
        if not user_progress:
            user_progress = UserPageProgress(page=self, user=user, places=[])
            first_place = Place.objects.filter(page=self, is_start=True).first()

            if not first_place:
                return None

            first_place.node_info = None
            
            if self.lesson:
                lesson_user = UserLessonProgress.objects.get(lesson=self.lesson, user=user)

                if not lesson_user.pages:
                    lesson_user.pages = []
                lesson_user.pages.append(UserPageProgressSerializer(user_progress).data)
                lesson_user.save()
            user_progress.places.append(PlaceUserInfoSerializer(first_place).data)
            user_progress.save()
        return user_progress

    def get_next_page(self, p_user, user):
        if self.lesson:
            lesson_user = UserLessonProgress.objects.get(lesson=self.lesson, user=user)
            for idx, page  in enumerate(lesson_user.pages):
                if self.id == int(page['page']):
                    lesson_user.pages[idx]['completed'] = True
            lesson_user.save()

        next_page = None
        if self.next_pages:
            next_pages = sorted(self.next_pages, key=lambda k: int(k['points']), reverse=True)
            for page in next_pages:
                if p_user.points >= int(page['points']):
                    next_page = page
                    break
        if next_page:
            p_user.next_page = int(next_page['page'])
            return int(next_page['page'])
        return None

    def __str__(self):
        onboarding_str = ''
        if self.is_onboarding_for:
            onboarding_str = ' онбординг для симулятора ' + str(self.is_onboarding_for.id)
        return '{} (id={}){}'.format(self.name, self.id, onboarding_str)



class UserPageProgress(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    utility = models.PositiveIntegerField(null=True, blank=True)
    places = JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)
    fun = models.PositiveIntegerField(null=True, blank=True)
    points = models.IntegerField(default=0)
    # first_uncompleted_place = models.ForeignKey(Place, on_delete=models.SET_NULL, null=True, blank=True)
    completed = models.BooleanField(default=False)
    is_test_passed = models.BooleanField(null=True, blank=True)
    is_show = models.BooleanField(default=False)
    next_page = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return '{} (user {})'.format(self.page, self.user)

    