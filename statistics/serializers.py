from rest_framework import fields, serializers
from pages.models import Page, UserPageProgress
from payments.models import Payment
from simulators.models import Simulator, SimulatorUser
from lessons.models import Lesson, UserLessonProgress
from django.db.models import Q, Avg
import logging
logger = logging.getLogger("django.server")

class MainInfoStatisticSerializer(serializers.ModelSerializer):
    users_completed_count = serializers.SerializerMethodField()
    users_try_pay_count = serializers.SerializerMethodField()
    users_paid_count = serializers.SerializerMethodField()
    users_count = serializers.SerializerMethodField()

    def get_users_completed_count(self, obj):
        return SimulatorUser.objects.filter(simulator=obj, simulator_completed=True).count()

    def get_users_try_pay_count(self, obj):
        return Payment.objects.filter(simulator=obj).count()

    def get_users_paid_count(self, obj):
        return SimulatorUser.objects.filter(simulator=obj, simulator_paid=True).count()

    def get_users_count(self, obj):
        return SimulatorUser.objects.filter(simulator=obj).count()
    
    class Meta:
        model = Simulator
        fields = ("users_completed_count", "users_try_pay_count", "users_paid_count", "users_count")
    
class PageUserStatisticSerializer(serializers.ModelSerializer):
    avg_fun = serializers.SerializerMethodField()
    avg_utility = serializers.SerializerMethodField()

    def get_avg_fun(self, obj):
        return list(UserPageProgress.objects.filter(page=obj).aggregate(Avg('fun')).values())[0]

    def get_avg_utility(self, obj):
        return list(UserPageProgress.objects.filter(page=obj).aggregate(Avg('utility')).values())[0]
    
    class Meta:
        model = Page
        fields = ("avg_fun", "avg_utility", "name")

class LessonInfoStatisticSerializer(serializers.ModelSerializer):
    pages_info = serializers.SerializerMethodField()
    users_lesson_complete = serializers.SerializerMethodField()

    def get_pages_info(self, obj):
        pages = Page.objects.filter(lesson=obj)
        pages_info = []
        for page in pages:
            page_info = {
                "name": page.name,
                "completed_users_count": UserPageProgress.objects.filter(page=page, completed=True).count()
            }
            pages_info.append(page_info)
        return pages_info
    
    def get_users_lesson_complete(self, obj):
        return UserLessonProgress.objects.filter(lesson=obj, completed=True).count()
    
    class Meta:
        model = Lesson
        fields = ("pages_info", "users_lesson_complete")

class MainUserStatisticSerializer(serializers.ModelSerializer):
    users_completed_count = serializers.SerializerMethodField()
    lessons_completed_count = serializers.SerializerMethodField()
    users_character_count = serializers.SerializerMethodField()
    users_onboarding_complete = serializers.SerializerMethodField()
    users_count = serializers.SerializerMethodField()

    def get_users_completed_count(self, obj):
        return SimulatorUser.objects.filter(simulator=obj, simulator_completed=True).count()

    def get_lessons_completed_count(self, obj):
        lessons = Lesson.objects.filter(simulator=obj).order_by('sequence_no')
        lessons_completed_count = []
        for lesson in lessons:
            lessons_completed_count.append(UserLessonProgress.objects.filter(lesson=lesson, completed=True).count())
        return lessons_completed_count

    def get_users_character_count(self, obj):
        return SimulatorUser.objects.filter(~Q(user__avatar=None) & ~Q(user__avatar=""), simulator=obj).count()

    def get_users_onboarding_complete(self, obj):
        return SimulatorUser.objects.filter(simulator=obj, onboarding_complete=True).count()

    def get_users_count(self, obj):
        return SimulatorUser.objects.filter(simulator=obj).count()


    class Meta:
        model = Simulator
        fields = ('users_completed_count', 'lessons_completed_count', 'users_character_count', 'users_onboarding_complete', 'users_count')