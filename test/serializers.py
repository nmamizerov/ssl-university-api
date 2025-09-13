from .models import Category, Context,Skill, CategorySkill, Result
from rest_framework import serializers, status

class CategorySerializer(serializers.ModelSerializer):
    skills = serializers.SerializerMethodField()
    def get_skills(self, obj):
        skills = CategorySkill.objects.filter(category=obj).all()
        if skills:
            return CategorySkillSerializer(skills, many=True).data
        return None
    class Meta:
        model = Category
        fields = '__all__'
        depth = 1
class ContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = Context
        fields = '__all__'
        depth = 1
class CategorySkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategorySkill
        fields = '__all__'
        depth = 1

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'
        depth = 1

class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = '__all__'
        depth = 1