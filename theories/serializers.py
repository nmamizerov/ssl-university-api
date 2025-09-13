from rest_framework import serializers
from .models import TheoryChapter
from places.serializers import PlaceUserInfoSerializer
from places.models import PlaceUser



class AdminTheoryChapterSerializer(serializers.ModelSerializer):
    
    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.sequence_no = instance.max_seq_no
        instance.save()
        return instance
        
    class Meta:
        model = TheoryChapter
        fields = '__all__'


class TheoryChapterSerializer(serializers.ModelSerializer):
    theories = serializers.SerializerMethodField()

    def get_theories(self, obj):
        u_places = PlaceUser.objects.filter(place__theory_chapter=obj, place__type="theory", user=self.context['request'].user, is_completed=True)
        places = []
        for place in u_places:
            places.append(place.place)
        return PlaceUserInfoSerializer(places, many=True).data
        
    class Meta:
        model = TheoryChapter
        fields = '__all__'
