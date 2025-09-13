from django.shortcuts import render
from .models import CompanyEmails, Company
from lessons.models import UserLessonProgress
from lessons.serializers import UserLessonProgressCompanySerializer
from pages.models import UserPageProgress
from pages.serializers import UserPageProgressSerializer
from .serializers import CompanyEmailsSerializer, CompanySerializer
from rest_framework import status
from rest_framework.views import APIView 
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q
from django.contrib.auth import get_user_model

User = get_user_model()
# Create your views here.
class GetCompanyEmails(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        if not request.user.company_admin:
            return Response('Нет прав у пользователя', status=status.HTTP_404_NOT_FOUND)
        emails = CompanyEmails.objects.filter(company = request.user.company).all()
        return Response(CompanyEmailsSerializer(
                emails, many=True).data,
            200
            )
    def post(self, request):
        permission_classes = [AllowAny]
        if not request.user.company_admin:
            return Response('Нет прав у пользователя', status=status.HTTP_404_NOT_FOUND)
        with transaction.atomic():
            items = request.data["emails"]
            for item in items:
                item = item.strip()
                if CompanyEmails.objects.filter(email=item).first() is None:
                    CompanyEmails.objects.create(email=item, company = request.user.company)
        return Response(status=status.HTTP_201_CREATED)

class CompanyEmail(APIView):
    permission_classes = [AllowAny]
    def delete(self, request, id):
        if not request.user.company_admin:
            return Response('Нет прав у пользователя', status=status.HTTP_404_NOT_FOUND)
        email = CompanyEmails.objects.filter(Q(pk=id) & Q(company = request.user.company)).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CompanyView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, slug):
        company = Company.objects.filter(slug=slug).first()
        return Response(CompanySerializer(
                company).data,
            200
            )

class GetCompanyStat(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if not request.user.company_admin:
            return Response('Нет прав у пользователя', status=status.HTTP_404_NOT_FOUND)
        users = User.objects.filter(company = request.user.company).all()
        lessons_completed = UserLessonProgress.objects.filter(Q(user__in=users)&Q(completed=True)).all().count()
        lessons_started = UserLessonProgress.objects.filter(Q(user__in=users)&~Q(pages=None)).all().count()
        return Response({"regs":users.count(),"lessons_completed":lessons_completed, "lessons_started":lessons_started},
            200
            )

class GetCompanyUserStat(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if not request.user.company_admin:
            return Response('Нет прав у пользователя', status=status.HTTP_404_NOT_FOUND)
        user = User.objects.filter(company = request.user.company, email = request.GET.get('email')).first()
        if user is None:
            return Response(request.GET.get('email'), status=status.HTTP_404_NOT_FOUND)
        lessons = UserLessonProgress.objects.filter(Q(user=user)&~Q(pages=None)).all()
        return Response(UserLessonProgressCompanySerializer(lessons, many=True).data,
            200
            )

class GetCompanyUserPage(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if not request.user.company_admin:
            return Response('Нет прав у пользователя', status=status.HTTP_404_NOT_FOUND)
        user = User.objects.filter(company = request.user.company, email = request.GET.get('email')).first()
        if user is None:
            return Response(request.GET.get('email'), status=status.HTTP_404_NOT_FOUND)
        u_p = UserPageProgress.objects.filter(Q(page=request.GET.get('page'))&Q(user=user)).first()
        return Response(UserPageProgressSerializer(u_p).data,
            200
            )
