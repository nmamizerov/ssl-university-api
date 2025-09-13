from rest_framework import fields, serializers
from .models import Company, CompanyEmails

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"

class CompanyEmailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyEmails
        exclude = ["company"]