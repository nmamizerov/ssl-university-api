from simulators.models import SimulatorUser
from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        avatar = None
        if obj.to_user.avatar:
            avatar = obj.from_user.avatar.url
        return {
            "first_name": obj.from_user.first_name,
            "last_name": obj.from_user.last_name,
            "avatar": avatar
        }

    class Meta:
        model = Notification
        fields = "__all__"
