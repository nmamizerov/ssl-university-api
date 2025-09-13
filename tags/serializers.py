from rest_framework import serializers, status

from lessons.models import Lesson
from .models import Tag


class AdminTagSerializer(serializers.ModelSerializer):
    lessons = serializers.PrimaryKeyRelatedField(many=True, queryset=Lesson.objects.all())

    class Meta:
        model = Tag
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField(read_only=True)

    def get_lessons(self, obj):
        from lessons.serializers import LessonSerializer

        lessons = Lesson.objects.filter(tag=obj)
        serializer = LessonSerializer(instance=lessons, context=self.context, many=True)
        return serializer.data

    class Meta:
        model = Tag
        fields = ('id', 'name', 'lessons', 'is_show')


class TagListingField(serializers.RelatedField):
    def to_representation(self, value):
        return value.name


class TagListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'is_show')


class TagPrimaryKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id',)
