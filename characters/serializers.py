from rest_framework import serializers
from .models import Character


class CharacterSerializer(serializers.ModelSerializer):
    social_role = serializers.CharField(default="", read_only=True)
    
    class Meta:
        model = Character
        fields = '__all__'