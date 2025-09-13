from .models import Course, Lesson
from rest_framework import serializers, status
from lessons.serializers import LessonSerializer as LS

class LessonSerializer(serializers.ModelSerializer): 
    lessons_data = serializers.SerializerMethodField()
    def get_lessons_data(self, obj):
        return LS(obj.lessons, many=True, context={'request': self.context['request']}).data
    class Meta:
        model = Lesson
        exclude = ['course', 'lessons']

class CourseSerializer(serializers.ModelSerializer): 
    
    class Meta:
        model = Course
        exclude = ['users']



class CourseSingleSerializer(serializers.ModelSerializer): 
    lessons = serializers.SerializerMethodField()
    def get_lessons(self, obj):
        lessons = Lesson.objects.filter(course=obj).all().order_by('order')
        if lessons:
            return LessonSerializer(lessons, many=True, context={'request': self.context['request']}).data
        return None
    class Meta:
        model = Course
        exclude = ['users']