from rest_framework import serializers
from .models import Place, PlaceUser
from characters.serializers import CharacterSerializer
from characters.models import Character
from django.db.models import Max
import logging
logger = logging.getLogger("django.server")


class PlaceJsonInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Place
        fields = '__all__'

class PlaceUserInfoSerializer(serializers.ModelSerializer):
    character = serializers.SerializerMethodField()
    parent_message = serializers.SerializerMethodField()

    def get_parent_message(self, obj):
        if obj.parent_message:
            return PlaceUserInfoSerializer(obj.parent_message).data
        return None
        
    def get_character(self, obj):
        if obj.character:
            character = obj.character
            if obj.forced_role:
                character.social_role = obj.forced_role
            else:
                character.social_role = character.default_role
            return CharacterSerializer(character).data
        return None

    class Meta:
        model = Place
        exclude = ("node_info", )


class PlaceSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.page.append_place(instance)
        return instance
    
    def update(self, instance, validated_data):
        updated_instance = super().update(instance, validated_data)
        updated_instance.page.update_place(updated_instance)
        return updated_instance

    class Meta:
        model = Place
        fields = '__all__'


class PlaceUserSerializer(serializers.ModelSerializer):
    answers = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    def get_answers(self, obj):
        if isinstance(obj.answers, int):
            return obj.place.answers[obj.answers]['text']

        if isinstance(obj.answers, str):
            return obj.answers

        if not obj.answers:
            return None

        return [obj.place.answers[answer]['text'] for answer in obj.answers]

    def get_first_name(self, obj):
        return obj.user.first_name

    def get_last_name(self, obj):
        return obj.user.last_name

    def get_email(self, obj):
        return obj.user.email

    class Meta:
        model = PlaceUser
        exclude = ("user", "points", "comments", "commented_by_user_set", "commented_count")
