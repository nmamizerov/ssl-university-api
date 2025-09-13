from django.shortcuts import render
from rest_framework.views import APIView 
from rest_framework.permissions import AllowAny
from .models import Course, Lesson
from .serializers import CourseSerializer, CourseSingleSerializer
from rest_framework.response import Response
from user_profile.permissions import UsersPermissions
from django.db.models import Q
from rest_framework import status

class GetCoursesData(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        if request.user.company is None:
            my_courses = Course.objects.filter(Q(users = request.user))
            active_courses = Course.objects.filter(~Q(users = request.user)&Q(show_front = True))
        else:
            my_courses = Course.objects.filter(Q(users = request.user) | Q(company = request.user.company) ).distinct()
            active_courses = None
            if request.user.company.show_default_courses:
                active_courses = Course.objects.filter(~Q(company = request.user.company)&~Q(users = request.user)&Q(show_front = True))
        
        return Response(
            {"my": CourseSerializer(
                my_courses, many=True).data, "active": CourseSerializer(
                active_courses, many=True).data}
            ,
            200
            )

class GetCourse(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        slug = request.GET.get('slug')
        course = Course.objects.filter(Q(slug = slug)&(Q(users = request.user)|Q(company = request.user.company))).first()
        if course is None:
            return Response('Нет прав у пользователя или нет курса', status=status.HTTP_404_NOT_FOUND)
        return Response(
            CourseSingleSerializer(
                course, context={'request': request}).data
            ,
            200
            )

class GetHomeCourses(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        slug = request.GET.get('slug')
        base_courses = Course.objects.filter(is_base=True).all()
        next_courses = Course.objects.filter(is_next=True).all()
        if request.user.company is None:
            my_courses = Course.objects.filter(Q(users = request.user))
            active_courses = Course.objects.filter(~Q(users = request.user)&Q(show_front = True))
        else:
            my_courses = Course.objects.filter(Q(users = request.user) | Q(company = request.user.company) ).distinct()
            active_courses = None
            if request.user.company.show_default_courses:
                active_courses = Course.objects.filter(~Q(company = request.user.company)&~Q(users = request.user)&Q(show_front = True))
        return Response(
            {"base": CourseSerializer(
                base_courses, many=True).data, "next": CourseSerializer(
                next_courses, many=True).data, "my": CourseSerializer(
                my_courses, many=True).data, "active": CourseSerializer(
                active_courses, many=True).data}
            ,
            200
            )