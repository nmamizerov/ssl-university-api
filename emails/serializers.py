from rest_framework import serializers
from .models import Email


class AdminEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = "__all__"
