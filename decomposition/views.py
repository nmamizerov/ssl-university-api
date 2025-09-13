from django.shortcuts import render
from rest_framework.views import APIView 
from rest_framework.permissions import AllowAny, IsAuthenticated 
from rest_framework.response import Response
from .models import FeedbackSituationUser, FeedbackSituation, FeedbackSituationUserMark
from .serializers import FeedbackSituationUserSerializer, FeedbackSituationUserMarkSerializer
from rest_framework import status
from django.db.models import Q
from bot.models import tgUser, tgSend
from subscriptions.models import UserSubscription
# import logging, json
# logging.basicConfig(filename='example.log', level=logging.DEBUG)

# Create your views here.
class GetDecomposition(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        if 'id' not in request.data: 
            return Response('Не передали id', status=status.HTTP_404_NOT_FOUND)
        id = request.data.get("id")
        u_f = FeedbackSituationUser.objects.filter(Q(user = request.user)&Q(pk = id)).first()
        if u_f is None: 
            return Response('Что-то не так с данными', status=status.HTTP_404_NOT_FOUND)
        u_f.answer = request.data.get("answer")
        count = FeedbackSituationUser.objects.filter(Q(situation = u_f.situation) & ~Q(user = request.user)&~Q(answer=None)).count()
        if count == 0:
            u_f.completed = True
        u_f.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    def put(self, request):
        if 'id' not in request.data: 
            return Response('Не передали id', status=status.HTTP_404_NOT_FOUND)
        id = request.data.get("id")
        u_f = FeedbackSituationUser.objects.filter(pk = id).first()
        if u_f is None: 
            return Response('Что-то не так с данными', status=status.HTTP_404_NOT_FOUND)
        u_f.marks += 1
        my_u_f = FeedbackSituationUser.objects.filter(Q(user=request.user)&Q(situation = u_f.situation)).first()
        my_u_f.my_count_marks += 1
        FeedbackSituationUserMark.objects.create(
            s_user = u_f, 
            comment = request.data.get("comment"), 
            mark = request.data.get("mark"), 
        )
        u_f.save()

        count = FeedbackSituationUser.objects.filter(Q(situation = u_f.situation) & ~Q(user = request.user)&~Q(answer=None)).count()
        if my_u_f.my_count_marks >= 2 or my_u_f.my_count_marks >= count :
            my_u_f.completed = True
        
        tg_user = tgUser.objects.filter(user=u_f.user).first()
        if tg_user is not None and tg_user.active: 
            message = f"""Вы получили комментарий на ваш ответ в упражнении по Разложению по смыслам: 
<b>{u_f.situation.text}</b>
<i>{u_f.situation.phrase}</i>

Ваш ответ: 
{u_f.answer}

Оценка: 
{request.data.get("mark")}
Комментарий:
<i>{request.data.get("comment")}</i>

<a href=\"https://skillslab.center/decomposition/{request.data.get("seq")}\">Перейти к ответу</a>"""
            tgSend.objects.create(
                    tg=tg_user,
                    message=message
                )

        my_u_f.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    def get(self, request):
        subscription = UserSubscription.objects.filter(user=request.user).first()
        if subscription is None:
            return Response(status=status.HTTP_402_PAYMENT_REQUIRED)
        if subscription.type<=4 or not subscription.subscription.is_blog:
            return Response(status=status.HTTP_402_PAYMENT_REQUIRED)
        situations = FeedbackSituation.objects.all().order_by('pk')
        count = situations.count()
        id = int(request.GET.get('id', -1))
        if id >= count: 
            return Response(1, status=status.HTTP_404_NOT_FOUND)

        situation = situations[id]
        if id != 0: 
            u_f_check = FeedbackSituationUser.objects.filter(Q(user = request.user)&Q(situation = situations[id-1])).first()
            if u_f_check is None or not u_f_check.completed:
                return Response(2, status=status.HTTP_404_NOT_FOUND)
            
        u_f = FeedbackSituationUser.objects.filter(Q(user = request.user)&Q(situation = situation)).first()
        completed = FeedbackSituationUser.objects.filter(Q(user = request.user)&Q(completed = True)).count()
        if u_f is None:
            u_f = FeedbackSituationUser.objects.create(
                situation = situation, 
                user = request.user
            )
        
        my_comments = FeedbackSituationUserMark.objects.filter(s_user = u_f).all()
        
        
        to_comment = FeedbackSituationUser.objects.filter(~Q(user = request.user)&Q(situation = situation)&~Q(answer=None)).order_by('marks', 'pk').first()

        return Response(
            {"feedback": FeedbackSituationUserSerializer(
                u_f).data, "count" : count, "completed": completed, "to_comment":FeedbackSituationUserSerializer(
                to_comment).data, 'comments': FeedbackSituationUserMarkSerializer(my_comments, many=True).data}
            ,
            200
            )