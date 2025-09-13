from places.models import PlaceUser
from places.serializers import PlaceUserSerializer
from simulators.models import SimulatorUser
from rest_framework import serializers
from .models import CommentRequest
from pages.models import UserPageProgress


class CommentRequestSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        user = self.context['request'].user
        if user.balance >= self.context['request'].simulator.admin_comment_request_price:
            user.balance = user.balance - self.context['request'].simulator.admin_comment_request_price
            user.save()
        else:
            raise serializers.ValidationError({
                    'score': 'У вас недостаточно баллов'
                })
        instance = super().create(validated_data)
        instance.user = self.context['request'].user
        instance.save()
        place_user = PlaceUser.objects.filter(place=instance.place, user=self.context['request'].user).first()
        page_user = UserPageProgress.objects.filter(page=instance.place.page, user=self.context['request'].user).first()
        if page_user:
            for idx, place in enumerate(page_user.places):
                if place['id'] == instance.place.id:              
                    page_user.places[idx]['admin_comment_requested'] = True
            page_user.save()

        if not place_user:
            raise serializers.ValidationError({
                    'user': 'Пользователь не ответил на вопрос'
                })
        place_user.admin_comment_requested = True
        place_user.save()
        return instance

    class Meta:
        model = CommentRequest
        fields = "__all__"
        read_only_fields = ("comment", 'commented')


class AdminCommentRequestSerializer(serializers.ModelSerializer):
    comment = serializers.SerializerMethodField()

    def get_comment(self, obj):
        place_user = PlaceUser.objects.filter(place=obj.place, user=obj.user).first()
        if place_user:
            return PlaceUserSerializer(place_user).data
        return None

    class Meta:
        depth=2
        model = CommentRequest
        fields = "__all__"
