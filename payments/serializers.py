from rest_framework import serializers
from .models import Payment, PromoCode
from simulators.models import Simulator


class PromoCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = "__all__"


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('id', 'creation_time', 'status')
