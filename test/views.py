from django.shortcuts import render
from rest_framework.views import APIView 
from rest_framework.permissions import AllowAny
from .models import Category, Context,Skill, Result
from .serializers import CategorySerializer, ContextSerializer, SkillSerializer, ResultSerializer
from rest_framework.response import Response
# Create your views here.
class GetMainData(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        categories = Category.objects.all().order_by('pk')
        contexts = Context.objects.all().order_by('pk')
        skill = Skill.objects.all().order_by('pk')
        result = Result.objects.filter(slug = request.GET.get('slug')).first()
        return Response(
            {"categories": CategorySerializer(
                categories, many=True).data, "contexts": ContextSerializer(
                contexts, many=True).data, "skill": SkillSerializer(
                skill, many=True).data, 
                "result":ResultSerializer(result).data}
            ,
            200
            )
