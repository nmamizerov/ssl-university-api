from rest_framework import serializers, status

from lessons.models import Lesson
from .models import Recommendation


class AdminRecommendationSerializer(serializers.ModelSerializer):
    lessons = serializers.PrimaryKeyRelatedField(many=True, queryset=Lesson.objects.all())

    class Meta:
        model = Recommendation
        fields = '__all__'


class RecommendationSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField(read_only=True)

    def get_lessons(self, obj):
        from lessons.serializers import LessonSerializer

        lessons = Lesson.objects.filter(tag=obj)
        serializer = LessonSerializer(instance=lessons, context=self.context, many=True)
        return serializer.data

    class Meta:
        model = Recommendation
        fields = "__all__"


class RecommendationListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        exclude = ('lessons',)
