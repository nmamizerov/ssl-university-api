from .models import tag, note
from rest_framework import serializers, status

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = tag
        fields = '__all__'
        depth = 1
class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = note
        fields = '__all__'
        depth = 1

        