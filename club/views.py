from django.shortcuts import render
from rest_framework.views import APIView 
from rest_framework.permissions import AllowAny
from user_profile.permissions import UsersPermissions
from rest_framework.response import Response
from .serializers import ClubSerializer, PlayerSerializer, TournamentSerializer
from user_profile.serializers import RatingSerializer
from subscriptions.models import UserSubscription
from django.contrib.auth import get_user_model
from django.db.models import Q
import boto3
from botocore.exceptions import ClientError
from .models import Club, Player, Game, Tournament
User = get_user_model()
class GetClubs(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        clubs = Club.objects.filter(show=True).order_by('name')
        return Response(ClubSerializer(
                clubs, many=True).data,
            200
            )
    def post(self, request):
        permission_classes = [UsersPermissions]
        request.user.member_id = request.data['club']
        request.user.save()
        return Response(request.data['club'],
            200
            )
class GetTournament(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        tours = Tournament.objects.filter(show=True).order_by('name')
        return Response(TournamentSerializer(
                tours, many=True).data,
            200
            )
class GetPlayers(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        player = Player.objects.all().order_by('name')
        return Response(PlayerSerializer(
                player, many=True).data,
            200
            )

class GetRating(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        users = User.objects.filter(rating_tournament__gt=0).order_by('-rating_tournament')
        count = request.GET.get('count')
        
        if count is not None:
            users = users[0:int(count)]
        else:
            users = users[0:15]
        return Response(RatingSerializer(
                users, many=True).data,
            200
            )


class GetRatingPK(APIView):
    permission_classes = [AllowAny]
    def get(self, request, id):
        users = User.objects.filter(pk=id).first()
        return Response(RatingSerializer(
                users).data,
            200
            )

