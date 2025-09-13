from rest_framework import serializers

from simulator_groups.serializers import SimulatorGroupInfoSerializer
from tags.serializers import TagListingSerializer
from .models import Simulator, SimulatorUser
from lessons.models import Lesson
from tags.models import Tag


class AdminSimulatorSerializer(serializers.ModelSerializer):
    css = serializers.SerializerMethodField(read_only=True)
    # css_text = serializers.CharField(write_only=True, allow_null=True, allow_blank=True)

    @staticmethod
    def get_css(obj):
        if obj.css:
            file = obj.css.open('r')
            text = file.read()
            file.close()
            return text
        return ""

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if 'css_text' in self.context['request'].data:
            instance.configure_css(self.context['request'].data['css_text'])
        else:
            instance.configure_css("")
        return instance

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.create_onboarding()        
        
        instance.sequence_no = instance.max_seq_no
        instance.save()
        return instance
    
    class Meta:
        model = Simulator
        exclude = ('completed_by_user_set',)


class SimulatorSerializer(serializers.ModelSerializer):
    tags = serializers.SerializerMethodField()

    def get_tags(self, obj):
        lessons = Lesson.objects.filter(simulator = obj).all()
        tags = Tag.objects.filter(lessons__in = lessons).distinct()
        return TagListingSerializer(instance=tags, many=True).data

    class Meta:
        model = Simulator
        exclude = ('completed_by_user_set', 'pay_terminal_key', 'pay_email_company', 'pay_password', 'token')


class SimulatorUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimulatorUser
        fields = "__all__"
