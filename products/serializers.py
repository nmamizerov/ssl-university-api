from rest_framework import serializers
from .models import Product


class AdminProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        exclude = ('users',)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        exclude = ('users', 'template', 'theme')
