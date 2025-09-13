from .models import FeedbackSituationUser, FeedbackSituation, FeedbackSituationUserMark
from rest_framework import serializers, status
from django.db.models import Q
class FeedbackSituationUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackSituationUser
        exclude = ['user']
        depth = 1

class FeedbackSituationUserMarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackSituationUserMark
        exclude = ['s_user']