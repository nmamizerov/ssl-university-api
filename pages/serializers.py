from rest_framework import serializers
from .models import Page, UserPageProgress
from django.db.models import Max
from lessons.serializers import LessonSerializer

class AdminPageSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.sequence_no = instance.max_seq_no
        instance.save()
        return instance
    
    class Meta:
        model = Page
        fields = '__all__'


class UserPageProgressSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    lesson_name = serializers.SerializerMethodField()
    page_name = serializers.SerializerMethodField()

    def get_page_name(self, obj):
        return obj.page.name

    def get_email(self, obj):
        return obj.user.email

    def get_lesson_name(self, obj):
        if obj.page.lesson:
            return obj.page.lesson.name
        return None
    class Meta:
        model = UserPageProgress
        fields = '__all__'

class PageSerializer(serializers.ModelSerializer):
    user_progress = serializers.SerializerMethodField()
    lesson_info = serializers.SerializerMethodField()

    def get_lesson_info(self, obj):
        return LessonSerializer(obj.lesson, context=self.context).data

    def get_user_progress(self, obj):
        user_progress = obj.get_user_progress(self.context['request'].user)
        if not user_progress:
            raise serializers.ValidationError({
                    'page': 'У страницы нет блока старта'
                })
        return UserPageProgressSerializer(user_progress).data
        
    class Meta:
        model = Page
        exclude = ('completed_by_user_set', 'is_onboarding_for', 'places')