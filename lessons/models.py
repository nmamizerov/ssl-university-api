from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.contrib.postgres.fields import JSONField
from simulators.models import Simulator
from user_profile.models import User
from django.db.models import Max

import logging
logger = logging.getLogger("django.server")


class Lesson(models.Model):
    name = models.CharField(max_length=200)
    price = models.PositiveIntegerField(default=5000)
    description = models.TextField(null=True, blank=True)
    full_info = models.TextField(null=True, blank=True)
    simulator = models.ForeignKey(Simulator, on_delete=models.CASCADE)
    active = models.BooleanField(default=False)
    picture = models.ImageField(
        verbose_name=('picture'), upload_to='lesson_pictures', null=True, blank=True
    )
    sequence_no = models.PositiveIntegerField(null=True)
    need_pause = models.BooleanField(blank=True, null=True)
    pause_length = models.IntegerField(blank=True, null=True)
    pause_text = models.TextField(blank=True, null=True)

    slug = models.CharField(blank=True, null=True, max_length=255, unique=True)
    time = models.IntegerField(blank=True, null=True)
    is_test = models.BooleanField(default = False)
    test_key = models.CharField(max_length = 30, blank=True)
    need_subscription = models.BooleanField(default=False)
    amount_places_without_subscription = models.IntegerField(blank=True, null=True)

    @property
    def max_seq_no(self):
        seq_no = Lesson.objects.filter(simulator=self.simulator).aggregate(Max("sequence_no"))['sequence_no__max']
        if seq_no:
            seq_no = seq_no + 1
        else:
            seq_no = 1
        return seq_no

    def is_user_owner(self, user):
        return self.simulator.group.owner == user

    def start(self, user):
        from pages.models import Page
        user_progress = UserLessonProgress()
        user_progress.user = user
        user_progress.lesson = self
        first_page = Page.objects.filter(lesson=self, is_start=True).first()
        if not first_page:
            return False
        user_progress.first_uncompleted_page = first_page
        user_progress.save()
        return True

    def get_user_progress(self, user):
        
        user_progress = UserLessonProgress.objects.filter(user=user, lesson=self).first()
        if not user_progress:
            page = self.pages.filter(is_start=True).first()
            if not page:
                return None
            user_progress = UserLessonProgress(user=user, lesson=self, first_uncompleted_page=page)
            user_progress.save()
            return user_progress
        return user_progress

    def get_next_lesson(self, user):
        lesson_user = UserLessonProgress.objects.filter(lesson=self, user=user).first()
        lesson_user.completed = True
        lesson_user.save()
        next_lesson = Lesson.objects.filter(sequence_no__gt=self.sequence_no).first()
        if next_lesson:
            return next_lesson.id
        return None

    def __str__(self):
        return '{} (id={})'.format(self.name, self.id)


class UserLessonProgress(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    pages = JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)
    first_uncompleted_page = models.ForeignKey('pages.page', on_delete=models.SET_NULL, null=True, blank=True)
    start_at = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return '{} (user {})'.format(self.lesson, self.user)
