from rest_framework import serializers

from recommendations.models import Recommendation
from recommendations.serializers import RecommendationListingSerializer
from tags.serializers import TagPrimaryKeySerializer, TagListingSerializer
from .models import Lesson, UserLessonProgress
from tags.models import Tag
import logging
logger = logging.getLogger("django.server")


class UserLessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLessonProgress
        fields = '__all__'

class UserLessonProgressCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLessonProgress
        fields = ['lesson', 'pages', 'completed']
        depth = 1


class AdminLessonSerializer(serializers.ModelSerializer):
    tags = serializers.SerializerMethodField()
    recommendations = serializers.SerializerMethodField()

    def get_recommendations(self, obj):
        recommendations = Recommendation.objects.filter(lessons=obj)
        return [recommendation.id for recommendation in recommendations]

    def get_tags(self, obj):
        tags = Tag.objects.filter(lessons=obj)
        return [tag.id for tag in tags]

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.sequence_no = instance.max_seq_no
        instance.save()
        return instance

    class Meta:
        model = Lesson
        fields = '__all__'


class LessonSerializer(serializers.ModelSerializer):
    user_progress = serializers.SerializerMethodField()
    order_active = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    recommendations = serializers.SerializerMethodField()

    def get_recommendations(self, obj):
        recommendations = Recommendation.objects.filter(lessons=obj)
        return RecommendationListingSerializer(instance=recommendations, many=True).data

    def get_tags(self, obj):
        tags = Tag.objects.filter(lessons=obj)
        return TagListingSerializer(instance=tags, many=True).data

    def get_order_active(self, obj):
        if not obj.simulator.order_lesson:
            return True
        lessons = UserLessonProgress.objects.filter(lesson__sequence_no__lt=obj.sequence_no, lesson__simulator=obj.simulator, user=self.context['request'].user)
        for lesson in lessons:
            if not lesson.completed:
                return False
        return True

    def get_user_progress(self, obj):
        return UserLessonProgressSerializer(obj.get_user_progress(self.context['request'].user)).data

    class Meta:
        model = Lesson
        fields = '__all__'
