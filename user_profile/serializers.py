import logging

from simulators.models import Simulator, SimulatorUser
from simulators.serializers import SimulatorUserSerializer
from rest_framework import fields, serializers
from django.contrib.auth import get_user_model
from simulator_groups.models import SimulatorGroup
from subscriptions.models import UserSubscription
from subscriptions.serializers import SubscriptionSerializer, UserSubscriptionSerializer
from company.serializers import CompanySerializer
from user_profile.models import AuthAttempt
from club.serializers import TournamentSerializer
from club.models import Tournament

User = get_user_model()
logger = logging.getLogger("django.server")


class AdminUserSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        instance = super(AdminUserSerializer, self).create(validated_data)
        instance.set_password(validated_data['password'])
        instance.is_admin_user = True
        instance.save()
        default_group = SimulatorGroup()
        default_group.owner = instance
        default_group.save()
        return instance

    def validate(self, data):
        if "re_password" not in self.context.get("request").data or data["password"] != self.context.get("request").data['re_password']:
            raise serializers.ValidationError({
                    're_password': 'Пароли не совпадают'
                })
        return data

    class Meta:
        model = User
        fields = '__all__'


class UserCreateSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        instance = super(UserCreateSerializer, self).create(validated_data)
        instance.set_password(validated_data['password'])
        simulators = Simulator.objects.filter(group=self.context['request'].simulator.group)
        logger.info(simulators)
        for simulator in simulators:
            sim_user = SimulatorUser(
                simulator=simulator,
                user=instance
            )
            sim_user.save()
        instance.save()

        self.context['request'].simulator.send_email(0, instance)
        return instance

    def validate(self, data):
        if "re_password" not in self.context.get("request").data or data["password"] != self.context.get("request").data['re_password']:
            raise serializers.ValidationError({
                    're_password': 'Пароли не совпадают'
                })
        return data

    class Meta:
        model = User
        fields = ("password", "username", "email", 'utm')


class UserInfoSerializer(serializers.ModelSerializer):
    sim_info = serializers.SerializerMethodField()
    auto_user = serializers.SerializerMethodField()
    filled = serializers.SerializerMethodField()
    subscription = serializers.SerializerMethodField()
    company = CompanySerializer()

    def get_subscription(self, obj):
        subscriptions = UserSubscription.objects.filter(user=obj)
        if not subscriptions.exists():
            return None

        subscription = subscriptions.first()
        if subscription.type < 5:
            return None

        return UserSubscriptionSerializer(subscription).data

    def get_auto_user(self, obj):
        subscriptions = UserSubscription.objects.filter(user=obj)
        if subscriptions.exists():
            if subscriptions.first().type == 0:
                return True
            return False
        return False

    def get_filled(self, obj):
        subscriptions = UserSubscription.objects.filter(user=obj)
        if subscriptions.exists():
            if subscriptions.first().type == 0:
                return False
            return True
        return False

    def get_sim_info(self, obj):
        sim_user = SimulatorUser.objects.filter(user=obj, simulator=self.context['request'].simulator).first()
        logger.info(obj)
        logger.info(self.context['request'].simulator)
        if sim_user:
            return SimulatorUserSerializer(sim_user).data
        return None

    def validate_email(self, value):
        user = self.context['request'].user
        simulator = self.context['request'].simulator

        if SimulatorUser.objects.filter(user__email=value, simulator=simulator).exclude(user=user).exists():
            raise serializers.ValidationError("Такая учетная запись уже существует")

        postfix = ''
        if simulator.group:
            postfix = '+{}'.format(simulator.group.id)
        user.username = value + postfix
        user.save()

        return value

    class Meta:
        model = User
        exclude = ("password", "username", 'user_permissions', 'groups', 'api_key', 'last_login', 'is_active', 'is_superuser', 'is_admin_user')


class ShortUserInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "id")

class RatingSerializer(serializers.ModelSerializer):
    # club_name = serializers.SerializerMethodField()
    # def get_club_name(self, obj):
    #     if obj.member is not None:
    #         return obj.member.name
    #     else: 
    #         return 'Нет клуба'
    place1 = serializers.SerializerMethodField()
    place2 = serializers.SerializerMethodField()
    place3 = serializers.SerializerMethodField()
    def get_place1(self, obj):
        t = Tournament.objects.filter(place1=obj.pk).all()
        return TournamentSerializer(t, many=True).data
    def get_place2(self, obj):
        t = Tournament.objects.filter(place2=obj.pk).all()
        return TournamentSerializer(t, many=True).data
    def get_place3(self, obj):
        t = Tournament.objects.filter(place3=obj.pk).all()
        return TournamentSerializer(t, many=True).data
    class Meta:
        model = User
        fields = ("first_name", "last_name", "id", "rating", "rating_fast", "rating_tournament", "rating_text_game", "place1", "place2", "place3")


class UserStatisticSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        return ShortUserInfoSerializer(obj.user).data
        
    class Meta:
        model = SimulatorUser
        fields = "__all__"


class AuthAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthAttempt
        fields = "__all__"
