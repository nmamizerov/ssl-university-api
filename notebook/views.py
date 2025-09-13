from django.shortcuts import render
from user_profile.permissions import UsersPermissions
from .models import note, tag
from django.db.models import Q
from rest_framework.response import Response
from .serializers import TagSerializer, NoteSerializer 
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
# Create your views here.

class GetNotebook(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        count = int(request.GET.get('count'))
        page = int(request.GET.get('page'))
        tag_id = request.GET.get('tag')
        if tag_id is not None: 
            tag_id = int(tag_id)
            tags = tag.objects.filter(user = request.user)
            notes = note.objects.filter(Q(tags__id = int(tag_id)) & Q(user = request.user))[count*(page-1):count*page]
            count = note.objects.filter(Q(tags__id = int(tag_id)) & Q(user = request.user)).count()
            return Response({"count":count, "tags": TagSerializer(tags, many=True).data, "notes": NoteSerializer(notes, many=True).data},
            200
            )
        else: 
            tags = tag.objects.filter(user = request.user)
            notes = note.objects.filter(user=request.user)[count*(page-1):count*page]
            count = note.objects.filter(user=request.user).count()
            return Response({"count":count, "tags": TagSerializer(tags, many=True).data, "notes": NoteSerializer(notes, many=True).data},
            200
            )

class GetNote(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        note_id = request.GET.get('note')
        my_note = note.objects.filter(id = int(note_id)).first()
        return Response({"note": NoteSerializer(my_note).data},
            200
            )
    def post(self, request):
        text = request.data['text']
        title = request.data['title']
        tags = request.data['tags']
        user = request.user
        my_note = note.objects.create(
            user=user,
            text=text, 
            title = title
        )
        for tag_id in tags: 
            tag_data = tag.objects.filter(Q(user=user)&Q(name =tag_id)).first()
            if tag_data is None:
                tag_data = tag.objects.create(
                    user = user, 
                    name = tag_id
                )
                my_note.tags.add(tag_data)
            else: 
                my_note.tags.add(tag_data)
        my_note.save()

        return Response('OK',
            200
            )

