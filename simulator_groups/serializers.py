from rest_framework import serializers
from .models import SimulatorGroup


class SimulatorGroupSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        instance = super(SimulatorGroupSerializer, self).create(validated_data)
        instance.owner = self.context.get('request').user
        instance.save()
        return instance

    class Meta:
        model = SimulatorGroup
        fields = '__all__'


class SimulatorGroupInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimulatorGroup
        exclude = ('auth_facebook_secret', 'auth_vk_secret', 'id')
