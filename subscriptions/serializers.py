from rest_framework import serializers
from .models import Subscription, UserSubscription


class AdminSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = "__all__"


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = "__all__"


class UserSubscriptionSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    is_blog = serializers.SerializerMethodField()
    is_club = serializers.SerializerMethodField()

    def get_is_blog(self, obj):
        return obj.subscription.is_blog
    def get_is_club(self, obj):
        return obj.subscription.is_club

    def get_id(self, obj):
        return obj.subscription.id

    def get_name(self, obj):
        return obj.subscription.name

    class Meta:
        model = UserSubscription
        fields = ('id', 'name', 'valid_until', 'resubscribe', 'is_blog', 'trial_expired', 'is_club')
