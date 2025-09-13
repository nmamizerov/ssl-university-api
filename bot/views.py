from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db.models import Q, Count
from .models import tgUser, tgSend, AITg
from decoding.models import Situation,SituationUser,userDecoding, SituationUserMark
from django.contrib.auth import get_user_model
from subscriptions.models import UserSubscription, Subscription
from datetime import timedelta, datetime, timezone
import json, requests
import logging
# logging.basicConfig(filename='example.log', level=logging.DEBUG)
User = get_user_model()
import math
import time
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = '5362028988:AAFNicUn5owN_OGq-JwdaTTG1g60eRtDlcM'
ADMIN_TOKEN = '5337404460:AAE5KsAga3pK3j5D3WabrihbdzUKTIusCU8'
TRAINER_TOKEN = '5831481117:AAF3ki3X4IwCR3D_UJxVkYQe1nuo-0Zid-w'
AI_TOKEN = '6985265483:AAFVoFtkQqojBwEXoJtHiRn67QtN6Slk6iQ'
AI_SERVICE_TOKEN = 'e1PNuQoPqhWimTEQfNZ78B710pvSqVR0'
AI_BASE_ENDPOINT = 'https://ml.skillslab.center/api/1/game/'


# Create your views here.

bot = telebot.TeleBot(TOKEN, threaded=False)
admin_bot = telebot.TeleBot(ADMIN_TOKEN, threaded=False, parse_mode='MARKDOWN')
trainer_bot = telebot.TeleBot(TRAINER_TOKEN, threaded=False, parse_mode='HTML')
ai_bot = telebot.TeleBot(AI_TOKEN, threaded=False, parse_mode='HTML')

def send_ext_course_info(id, text):
    admin_bot.send_message(id, text, parse_mode='HTML')

# Игра декодирование
def decoding(command, chat_id, message_id, tg_user):
    if command == 'start':
        decoding_start(chat_id, message_id, tg_user)
        return
    if command == 'leaders': 
        show_decoding_leaders(chat_id, tg_user)
        return
    if command == 'next':
        decoding_start(chat_id,message_id, tg_user)
        return
    try:
        com, id = command.split('&', 1) 
        if com == "plus":
            get_mark_decoding(True,id, chat_id, message_id, tg_user)
            return
        if com == "minus":
            get_mark_decoding(False,id, chat_id, message_id, tg_user)
            return
        if com == "best":
            get_best_answers(id, chat_id, message_id, tg_user)
            return
        if com == "author":
            show_author_answer(id, chat_id, message_id, tg_user)
            return

    except:
        pass

def show_decoding_leaders(chat_id, tg_user):
    user = userDecoding.objects.filter(user = tg_user.user).first()
    text = ""
    if user is not None:
        text += f"Ваш результат: {user.points} очков\n\n"
    users = userDecoding.objects.all().order_by('-points')[0:5]
    counter = 1
    for item in users:
        text+= f"{counter}. {item.user.first_name} {item.user.last_name}: {item.points}\n"
        counter+=1
    bot.send_message(chat_id, text, parse_mode="HTML")
    
def show_author_answer(id, chat_id, message_id, tg_user):
    situation = Situation.objects.filter(id = id).first()
    markup= aftertask_keyboard(id)
    bot.edit_message_text(f"Ответ автора: {situation.answer}", chat_id, message_id, reply_markup = markup, parse_mode="HTML")
def get_best_answers(id, chat_id, message_id, tg_user):
    answer_data = SituationUser.objects.filter(Q(situation__id = id)& Q(points__gt=1)).order_by('-points')[0:5]
    markup= aftertask_keyboard(id)
    if not answer_data:
        bot.edit_message_text('Пока что тут нет лучших ответов', chat_id, message_id, reply_markup = markup)
        return
    text = "<i>Лучшие ответы:</i>\n"
    counter = 1
    for item in answer_data:
        text = text + f"{counter}. {item.points}({item.marks}): {item.answer}\n"
        counter += 1
    bot.edit_message_text(text, chat_id, message_id, reply_markup = markup, parse_mode="HTML")

def aftertask_keyboard(id):
    return InlineKeyboardMarkup([
            [InlineKeyboardButton(text='Следующая задача', callback_data=f"decoding?next"), InlineKeyboardButton(text='Лучшие ответы', callback_data=f"decoding?best&{id}")], [InlineKeyboardButton(text='Ответ автора', callback_data=f"decoding?author&{id}")]
        ])

def get_mark_decoding(add, id, chat_id, message_id, tg_user):
    answer_data = SituationUser.objects.filter(pk = id).first()
    answer_data.marks = answer_data.marks+1

    if add:
        answer_data.points = answer_data.points+1
        d_user = userDecoding.objects.filter(user = answer_data.user).first()
        if d_user is not None:
            d_user.points = d_user.points + 1
            d_user.save()
    answer_data.save()
    last_game = SituationUser.objects.filter(user = tg_user.user).last()
    last_game.my_count_marks = last_game.my_count_marks+1
    last_game.save()
    SituationUserMark.objects.create(
        s_user = last_game, 
        mark_id = id
    )
    if last_game.my_count_marks >= 3:
        markup= aftertask_keyboard(last_game.situation.id)
        bot.edit_message_text('Спасибо за ваши оценки', chat_id, message_id, reply_markup = markup)
        return
    else:
        answer = get_answer_to_decoding(last_game.situation.id, last_game.my_count_marks, tg_user.user, last_game)
        if answer is None:
            markup= aftertask_keyboard(last_game.situation.id)
            bot.edit_message_text('Спасибо за ваши оценки', chat_id, message_id, reply_markup = markup)
            return
        else:
            markup = mark_decoding(answer.id)
            situation_text = f"{last_game.situation.text}\n<b>{last_game.situation.phrase}</b>\n\n<i>Оцените еще один ответ участника {last_game.my_count_marks+1} из 3</i>\n\n<i>{answer.answer}</i>"
            bot.edit_message_text(situation_text, chat_id, message_id, reply_markup = markup, parse_mode="HTML")

def decoding_handle_answer(chat_id, text, tg_user):
    last_game = SituationUser.objects.filter(user = tg_user.user).last()
    last_game.answer = text
    last_game.save()
    answer = get_answer_to_decoding(last_game.situation.id, last_game.my_count_marks, tg_user.user, last_game)
    if answer is None: 
        markup= aftertask_keyboard(last_game.situation.id)
        bot.send_message(chat_id, 'Пока что никто не ответил на этот вопрос, так что вы можете посмотреть ответ автора', reply_markup = markup)
        # new_situation(chat_id, tg_user)
        return 
    markup = mark_decoding(answer.id)
    situation_text = f"<i>Чтобы продолжить Вам нужно оценить декодирование другого участника</i>\n{last_game.situation.text}\n<b>{last_game.situation.phrase}</b>\n\n<i>{answer.answer}</i>"
    bot.send_message(chat_id, situation_text, reply_markup = markup, parse_mode="HTML")
    tg_user.command = None
    tg_user.value = None
    tg_user.save()

def new_situation(chat_id, tg_user):
    user_d = userDecoding.objects.filter(user = tg_user.user).first()
    if user_d is None: 
        userDecoding.objects.create(
            user = tg_user.user
        )
    already = SituationUser.objects.filter(user = tg_user.user).values_list('situation__id', flat=True)
    situation = Situation.objects.exclude(pk__in = already).first()
    if situation is not None:
        situation_text = f"<i>Вопрос {situation.id}</i>\n{situation.text}\n<b>{situation.phrase}</b>"
        tg_user.command = "decoding"
        tg_user.value = situation.id
        tg_user.save()
        SituationUser.objects.create(
            user = tg_user.user, 
            situation = situation
        )
        bot.send_message(chat_id, situation_text, parse_mode="HTML")
        return

    else:
        markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(text='Таблица лидеров', callback_data="decoding?leaders")]
        ])
        bot.send_message(chat_id, "Вы прошли все ситуации", reply_markup = markup)

def mark_decoding(id):
    markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(text='Верно', callback_data=f"decoding?plus&{id}"), InlineKeyboardButton(text='Неверно', callback_data=f"decoding?minus&{id}")]
        ])
    return markup

def get_answer_to_decoding(id, marks, user, s_user): 
    su_exclude = SituationUserMark.objects.filter(s_user = s_user).values_list('mark_id', flat=True)
    count = SituationUser.objects.filter(Q(situation__id = id)&Q(answer__isnull=False)).count()
    if marks+1 >= count: 
        return None
    answer = SituationUser.objects.filter(Q(situation__id = id)&~Q(id__in=su_exclude) &Q(answer__isnull=False)&~Q(user=user)).order_by('marks').first()
    if answer is not None:
        return answer
    else: 
        return None

def decoding_start(chat_id, message_id, tg_user):
    last_game = SituationUser.objects.filter(user = tg_user.user).last()
    if last_game is not None:
        if last_game.answer is not None:
            if last_game.my_count_marks < 3:
                answer = get_answer_to_decoding(last_game.situation.id, last_game.my_count_marks, tg_user.user, last_game)
                if answer is not None:
                    markup = mark_decoding(answer.id)
                    situation_text = f"<i>Чтобы продолжить Вам нужно оценить декодирование другого участника</i>\n{last_game.situation.text}\n<b>{last_game.situation.phrase}</b>\n\n<i>{answer.answer}</i>"
                    bot.send_message(chat_id, situation_text, reply_markup = markup, parse_mode="HTML")
                    return
                else:
                    new_situation(chat_id, tg_user)  
            else: 
                new_situation(chat_id, tg_user)
        else:
            tg_user.command = "decoding"
            tg_user.value = last_game.situation.id
            tg_user.save()
            situation_text = f"<i>Вопрос {last_game.situation.id}</i>\n{last_game.situation.text}\n<b>{last_game.situation.phrase}</b>"
            bot.send_message(chat_id, situation_text, parse_mode="HTML")
    else: 
        new_situation(chat_id, tg_user)

def decoding_leaders(chat_id, message_id, user):
    return

# Конец игры декодирование

def main_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
    itembtn1 = telebot.types.KeyboardButton('Тренировка декодирования')
    itembtn2 = telebot.types.KeyboardButton('Тренировка обратной связи')
    markup.add(itembtn1, itembtn2)
    return markup

def tg_user_exists(chat_id):
    tg = tgUser.objects.filter(chat_id=chat_id).first()
    if tg is not None: 
        return tg
    else: 
        return None
def send_inactive(chat_id):
    markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text='Оформить', url=f"https://skillslab.center/pricing")]
            ])
    bot.send_message(chat_id, "Чтобы воспользоваться функцией, оплатите, пожалуйста подписку.", reply_markup=markup)
def has_subscription(tg_user):
    sub = UserSubscription.objects.filter(user = tg_user.user).first()
    if sub is not None and sub.type >= 5 and sub.subscription.is_blog:
        return True
    else:
        return False

def user_exists(email):
    user = User.objects.filter(email__iexact=email).first()
    if user is not None: 
        return user
    else: 
        return None

def create_tg_user(user, chat_id):
    tgUser.objects.create(
        user=user,
        chat_id=chat_id
    )

def create_send(tg_user, message ):
    tgSend.objects.create(
        tg=tg_user,
        message=message
    )

def ai_request(endpoint, value=None, method='get'): 
    data = value
    headers = {'Authorization': 'Bearer ' + AI_SERVICE_TOKEN, "Content-Type": "application/json"}
    jsonStr = json.dumps(data)
    if method == "post":
        response = requests.post(AI_BASE_ENDPOINT+endpoint, headers = headers, data=jsonStr)
    else:
        response = requests.get(AI_BASE_ENDPOINT+endpoint, headers = headers, data=jsonStr)
    # logging.debug(1)
    # logging.debug(response)
    return response.json()


class AIBot(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        if request.META['CONTENT_TYPE'] == 'application/json':
    
            json_data = request.body.decode('utf-8')
            update = telebot.types.Update.de_json(json_data)
            ai_bot.process_new_updates([update])

            return HttpResponse("")

        else:
            raise PermissionDenied

class Bot(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        if request.META['CONTENT_TYPE'] == 'application/json':
    
            json_data = request.body.decode('utf-8')
            update = telebot.types.Update.de_json(json_data)
            bot.process_new_updates([update])

            return HttpResponse("")

        else:
            raise PermissionDenied

class TrainerBot(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        if request.META['CONTENT_TYPE'] == 'application/json':
    
            json_data = request.body.decode('utf-8')
            update = telebot.types.Update.de_json(json_data)
            trainer_bot.process_new_updates([update])

            return HttpResponse("")

        else:
            raise PermissionDenied
# class Temp(APIView):
#     permission_classes = [AllowAny]
#     def post(self, request, *args, **kwargs):
#         data = request.data['data']
#         for item in data:
#             Situation.objects.create(
#                 text=item["situation"],
#                 phrase=item["phrase"],
#                 answer = item["answer"]
#             )
#         return HttpResponse()

class BotAdmin(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        if request.META['CONTENT_TYPE'] == 'application/json':
    
            json_data = request.body.decode('utf-8')
            update = telebot.types.Update.de_json(json_data)
            admin_bot.process_new_updates([update])

            return HttpResponse("")

        else:
            raise PermissionDenied


# ai_bot
@ai_bot.message_handler(commands=['start'])
def get_okn(message):
    tg = AITg.objects.filter(chat_id = message.chat.id).first()

    if tg is None: 
        AITg.objects.create(
            chat_id = message.chat.id
        )
    data = ai_request('projects/')
    markup = InlineKeyboardMarkup()
    k=0
    if len(data) == 0:
        ai_bot.send_message(message.chat.id, "Нет проектов")
        return
    for k in range(0,math.ceil(len(data)//2)):
        if  k+1 != math.ceil(len(data)//2) or len(data)%2==0:
            markup.add(InlineKeyboardButton(data[k*2]['name'], callback_data=f"game?{data[k*2]['pk']}"),InlineKeyboardButton(data[k*2+1]['name'], callback_data=f"game?{data[k*2+1]['pk']}"))
        else:
            markup.add(InlineKeyboardButton(data[k*2]['name'], callback_data=f"game?{data[k*2]['pk']}"))
    ai_bot.send_message(message.chat.id, "Список сделанных игр", reply_markup=markup)

@ai_bot.callback_query_handler(func=lambda call: True)
def soution(inline_query):
    try:
        key, command = inline_query.data.split('?', 1)
    except: 
        return
    if key == 'game': 
        ai_bot.edit_message_text('Игра запускается', inline_query.message.chat.id, inline_query.message.id, reply_markup = None)
        ai_bot.send_chat_action(inline_query.message.chat.id, 'typing')
        tg = AITg.objects.filter(chat_id = inline_query.message.chat.id).first()
        # logging.debug(tg)
        data = ai_request(f'start/{command}')
        tg.value = data['game']
        tg.save()
        ai_bot.send_message(inline_query.message.chat.id, data['description'])
        ai_bot.send_chat_action(inline_query.message.chat.id, 'typing')
        time.sleep(1)
        ai_bot.send_message(inline_query.message.chat.id, data['phrase'])

@ai_bot.message_handler(func=lambda message: True)
def func(message):
    ai_bot.send_chat_action(message.chat.id, 'typing')
    
    ai_bot.send_chat_action(message.chat.id, 'typing')
    tg = AITg.objects.filter(chat_id = message.chat.id).first()
    if tg.value is None or int(tg.value) == 0:
        ai_bot.send_message(message.chat.id, "Начните любую игру нажав например /start")
    else:
        # logging.debug(24)
        data = ai_request(f'next/', {"pk": int(tg.value), "phrase":message.text}, "post")
        # logging.debug(data)
        ai_bot.send_message(message.chat.id, data["new_phrase"])
        if data["is_finished"]:
            tg.value = None
            tg.save()
            ai_bot.send_message(message.chat.id, data["comment"])

# end ai_bot
@bot.message_handler(commands=['start'])
def get_okn(message):
    tg_user = tg_user_exists(message.chat.id)
    if tg_user is not None: 
        tg_user.active = True
        tg_user.command = None
        tg_user.value = None
        tg_user.save()
        markup = main_keyboard()
        bot.send_message(message.chat.id, f"{tg_user.user.first_name}, мы рады видеть в боте Soft Skills Lab. Здесь вы получите уведомление о том, что вышел новый симулятор и что ваш ответ прокомментировали", reply_markup=markup)
        return
    try:
        command, email =  message.text.split(' ')
        user = user_exists(email)
        if user is not None:
            create_tg_user(user, message.chat.id)
            markup = main_keyboard()
            bot.send_message(message.chat.id, f"{user.first_name}, добро пожаловать!\nТеперь я могу отправлять вам уведомления", reply_markup=markup)
            return
        else:
            bot.send_message(message.chat.id, 'Такого пользователя нет')
            return

    except: 
        bot.send_message(message.chat.id, "Добро пожаловать в бот Soft Skills Lab. \nЯ умею оповещать о новых симуляторах, занятиях, играх и ответах на ваши комментарии\nВведите Ваш email, чтобы мы могли начать!")
        return
@bot.message_handler(commands=['cancel'])
def get_okn(message):  
    tg_user = tg_user_exists(message.chat.id)
    tg_user.command = ''
    tg_user.value = None
    tg_user.save()
    markup = main_keyboard()
    bot.send_message(message.chat.id, 'Всё сброшено', reply_markup=markup)
@bot.message_handler(commands=['delete'])
def get_okn(message):  
    tg_user = tg_user_exists(message.chat.id)
    if tg_user is not None:
        tg_user.delete()
        bot.send_message(message.chat.id, "Добро пожаловать в бот Soft Skills Lab. \nЯ умею оповещать о новых симуляторах, занятиях, играх и ответах на ваши комментарии\nВведите Ваш email, чтобы мы могли начать!", reply_markup=telebot.types.ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, "Эта команда неактивна")

@bot.message_handler(func=lambda message: message.text=="Тренировка декодирования")
def get_okn(message):  
    tg_user = tg_user_exists(message.chat.id)
    if tg_user is not None:
        if has_subscription(tg_user):
            markup = InlineKeyboardMarkup()
            markup.row_width = 2
            markup.add(InlineKeyboardButton("Начать", callback_data="decoding?start"),InlineKeyboardButton("Таблица лидеров", callback_data="decoding?leaders"))
            markup.add(InlineKeyboardButton("Симулятор декодирования", url="https://skillslab.center/blogs/decoding"),InlineKeyboardButton("Симулятор практики декодирования", url="https://skillslab.center/blogs/decoding_practice"))
            bot.send_message(message.chat.id, "В этом упражнении вам предстоит написать декодирование конфликта и после этого оценить декодирования других. За одобрение других участников вы получаете +1 балл.\n\n Чтобы трениовка была полезной, пройдите рекомендуемые симуляторы", reply_markup=markup)
            return
        else: 
            send_inactive(message.chat.id)
            return
    else:
        bot.send_message(message.chat.id, "Эта команда неактивна")
        return
@bot.message_handler(func=lambda message: message.text=="Тренировка обратной связи")
def get_okn(message):  
    tg_user = tg_user_exists(message.chat.id)
    if tg_user is not None:
        if has_subscription(tg_user):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Тренировка обратной связи", url="https://skillslab.center/feedback/0"))
            bot.send_message(message.chat.id, "В этом упражнении вам предстоит дать обратную связь по случайной схеме, которую вам нужно обязательно выполнить", reply_markup=markup)
            return
        else: 
            send_inactive(message.chat.id)
            return
    else:
        bot.send_message(message.chat.id, "Эта команда неактивна")
        return
@bot.callback_query_handler(func=lambda call: True)
def soution(inline_query):
    tg_user = tg_user_exists(inline_query.message.chat.id)
    try:
        key, command = inline_query.data.split('?', 1)
    except: 
        pass
    if key == 'decoding': 
        if tg_user is None:
            bot.edit_message_text('Вы незарегистрированы', inline_query.message.chat.id, inline_query.message.id)
            return
        if has_subscription(tg_user):
            decoding(command, inline_query.message.chat.id, inline_query.message.id, tg_user)
        else:
            send_inactive(inline_query.message.chat.id)

@bot.message_handler(func=lambda message: True)
def func(message):
    tg_user = tg_user_exists(message.chat.id)
    if tg_user is None:
        user = user_exists(message.text)
        if user is not None:
            create_tg_user(user, message.chat.id)
            markup = main_keyboard()
            bot.send_message(message.chat.id, f"{user.first_name}, добро пожаловать!\nТеперь я могу отправлять вам уведомления", reply_markup=markup)
            return
        else:
            bot.send_message(message.chat.id, 'Такого пользователя нет')
            return
    else: 
        if tg_user.command == "decoding": 
            decoding_handle_answer(message.chat.id, message.text, tg_user)
            return
        bot.send_message(message.chat.id, f"Понимаю, что покажусь глупым, я не понимаю о чем вы меня просите...")
        return

@admin_bot.message_handler(commands=['start'])
def get_okn(message):
    tg_user = tg_user_exists(message.chat.id)
    if tg_user is None:
        admin_bot.send_message(message.chat.id, f"Введите специальный email")
    else:
        if tg_user.user.is_staff:
            markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
            itembtn1 = telebot.types.KeyboardButton('Рассылка')
            itembtn2 = telebot.types.KeyboardButton('Подписок')
            itembtn3 = telebot.types.KeyboardButton('Людей')
            markup.add(itembtn1, itembtn2, itembtn3)
            admin_bot.send_message(message.chat.id, f"Ты уже зареган", reply_markup = markup)
        else:
            admin_bot.send_message(message.chat.id, f"Ты не админ")

@admin_bot.message_handler(commands=['send'])
def get_okn(message):
    sends = tgSend.objects.all()[:30]
    for send in sends: 
        try: 
            bot.send_message(send.tg.chat_id, send.message, parse_mode="HTML")
            send.delete()
        except Exception as e:
            send.tg.active = False
            send.tg.save()

@admin_bot.message_handler(commands=['cancel'])
def get_okn(message):
    tg_user = tg_user_exists(message.chat.id)
    if tg_user is not None:
        markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
        itembtn1 = telebot.types.KeyboardButton('Рассылка')
        itembtn2 = telebot.types.KeyboardButton('Подписок')
        itembtn3 = telebot.types.KeyboardButton('Людей')
        markup.add(itembtn1, itembtn2, itembtn3)
        admin_bot.send_message(message.chat.id, f"Отменили", reply_markup = markup)

@admin_bot.message_handler(func=lambda message: message.text=='Рассылка')
def new_item(message):
    tg_user = tg_user_exists(message.chat.id)
    if tg_user is None or not tg_user.user.is_staff:
        admin_bot.send_message(message.chat.id, f"Ты не админ")
        return
    tg_user.command = 'Рассылка'
    tg_user.save()
    admin_bot.send_message(message.chat.id, f"Введи сообщение для всех")

@admin_bot.message_handler(func=lambda message: message.text=='Подписок')
def new_item(message):
    subs = UserSubscription.objects.filter(type__gte = 5).count()
    subs_count = UserSubscription.objects.filter(type__gte = 5).values('subscription').annotate(total=Count('subscription')).order_by('total')
    txt = f'Количество подписок: {subs}\n'
    for sub in subs_count:
        value = Subscription.objects.filter(pk = sub['subscription']).first()
        if value is not None:
            txt += f"""{value.name}: {sub["total"]}

"""
    admin_bot.send_message(message.chat.id, txt, parse_mode="HTML")

@admin_bot.message_handler(func=lambda message: message.text=='Людей')
def new_item(message):
    subs = Subscription.objects.all()
    markup = InlineKeyboardMarkup()
    for sub in subs: 
        markup.row_width = 1
        markup.add(InlineKeyboardButton(sub.name, callback_data="sub@"+str(sub.id)))
    admin_bot.send_message(message.chat.id, "Выберите тип подписки", reply_markup=markup)

@admin_bot.callback_query_handler(func=lambda call: True)
def soution(inline_query):
    type, data = inline_query.data.split('@', 1)
    if type == "sub": 
        subs = UserSubscription.objects.filter(Q(type__gte = 5)&Q(subscription__id=data))
        text = "Подписчики:\n"
        for sub in subs:
            text =text + f"{sub.user.last_name} {sub.user.first_name}, "
        admin_bot.send_message(inline_query.message.chat.id, text)

@admin_bot.message_handler(func=lambda message: True)
def func(message):
    tg_user = tg_user_exists(message.chat.id)
    if tg_user is None:
        user = user_exists(message.text)
        if user is not None and user.is_staff:
            create_tg_user(user, message.chat.id)
            markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
            itembtn3 = telebot.types.KeyboardButton('Людей')
            markup.add(itembtn1, itembtn2, itembtn3)
            admin_bot.send_message(message.chat.id, f"{user.first_name}, добро пожаловать!\nТеперь у тебя есть власть", reply_markup = markup)
            return
        else:
            admin_bot.send_message(message.chat.id, 'Такого пользователя нет')
            return
    else: 
        if not tg_user.user.is_staff:
            admin_bot.send_message(message.chat.id, f"Ты не админ")
            return
        if tg_user.command == 'Рассылка':
            for tg in tgUser.objects.filter(active=True).all():
                create_send(tg, message.text)

            admin_bot.send_message(message.chat.id, f"Отправлено")
            tg_user.command = None
            tg_user.save()
            return

        admin_bot.send_message(message.chat.id, f"Понимаю, что покажусь глупым, я не понимаю о чем вы меня просите...")
        return




#  Тут все для бота для тренеров
def check_user_by_id(chat_id):
    user = User.objects.filter(tg_trainer_chat_id = chat_id).first()
    if user is None:
        return None
    else:
        return user
def check_user_by_token(token,chat_id):
    if token == '' or token is None:
        return None
    user = User.objects.filter(tg_trainer_code = token).first()
    if user is None:
        return None
    else:
        user.tg_trainer_chat_id = chat_id
        user.tg_trainer_code = None
        user.save()
        return user
@trainer_bot.message_handler(commands=['start'])
def get_okn(message):
    user = check_user_by_id(message.chat.id)
    if user is None:
        trainer_bot.send_message(message.chat.id, f"Введите код, который вы получили у администратора сайта")
        return
    else:
        trainer_bot.send_message(message.chat.id, f"Теперь у тебя есть власть давать подписки по команде /sub_add и проверять список подписок по команде /sub_check")
    

@trainer_bot.message_handler(commands=['sub_check'])
def get_okn(message):
    user = check_user_by_id(message.chat.id)
    if user is None:
        trainer_bot.send_message(message.chat.id, f"Нет права открывать подписки! Введите код, который вы получили у администратора сайта")
        return
    students = UserSubscription.objects.filter(trainer = user).all()
    text = "<b>Данные о подписках:\n</b>"
    for s in students:
        text += f"{s.user.email}: {s.valid_until.strftime('%d-%m-%Y')}\n"
    trainer_bot.send_message(message.chat.id, text)

@trainer_bot.message_handler(commands=['rating_add'])
def get_okn(message):
    user = check_user_by_id(message.chat.id)
    if user is None:
        trainer_bot.send_message(message.chat.id, f"Нет права добавлять рейтинг")
        return
    data = message.text.split()   
    if len(data) != 3: 
        trainer_bot.send_message(message.chat.id, """Напишите команду по формуле /rating_add points email 
Где email — email вашего ученика (проверяйте большие/маленькие буквы), points — число очков, которые надо добавить
Пример /rating_add 10 yg@klimenko.info
""")
        return
    student = User.objects.filter(email = data[2]).first()
    if student is None:
        trainer_bot.send_message(message.chat.id, f"Такого пользователя не существует!")
        return
    
    student.rating_tournament += int(data[1])
    student.save()
    trainer_bot.send_message(message.chat.id, f"Сохранили!")
    

@trainer_bot.message_handler(commands=['sub_delete'])
def get_okn(message):
    user = check_user_by_id(message.chat.id)
    if user is None:
        trainer_bot.send_message(message.chat.id, f"Нет права открывать подписки! Введите код, который вы получили у администратора сайта")
        return
    data = message.text.split()   
    if len(data) != 2: 
        trainer_bot.send_message(message.chat.id, """Напишите команду по формуле /sub_delete email
Где email — email вашего ученика (проверяйте большие/маленькие буквы)
Пример /sub_delete yg@klimenko.info
""")
        return
    student = User.objects.filter(email = data[1]).first()
    if student is None:
        trainer_bot.send_message(message.chat.id, f"Такого пользователя не существует!")
        return    
    sub = UserSubscription.objects.filter(user = student).first()
    if sub is not None:
        sub.type = 2
        sub.subscription = None
        sub.trainer = None
        sub.valid_until = None
        sub.save()
    
    trainer_bot.send_message(message.chat.id, "Доступ пользователю закрыт")

@trainer_bot.message_handler(commands=['sub_add'])
def get_okn(message):
    user = check_user_by_id(message.chat.id)
    if user is None:
        trainer_bot.send_message(message.chat.id, f"Нет права открывать подписки! Введите код, который вы получили у администратора сайта")
        return
    data = message.text.split()

    if len(data) != 3: 
        trainer_bot.send_message(message.chat.id, """Напишите команду по формуле /sub_add x email
Где x — число месяцев, на которое открываете доступ, а email — email вашего ученика (проверяйте большие/маленькие буквы)
Пример /sub_add 3 yg@klimenko.info
""")
        return
    student = User.objects.filter(email = data[2]).first()
    if student is None:
        trainer_bot.send_message(message.chat.id, f"Такого пользователя не существует!")
        return

    sub = UserSubscription.objects.filter(user = student).first()
    if(sub.type>=5):
        try:
            sub.valid_until = sub.valid_until + timedelta(days=30*int(data[1]))
            sub.trainer = user
            sub.save()
            trainer_bot.send_message(message.chat.id, "Так как у пользователя уже была активная подписка, была продлена именно она")
            return
        except Exception as e:
            trainer_bot.send_message(message.chat.id, "Что-то пошло не так")
            return
    else:
        try:
            sub.valid_until = datetime.now(timezone.utc) + timedelta(days=30*int(data[1]))
            sub.subscription_id = 16
            sub.type = 6
            sub.trainer = user
            sub.save()
            trainer_bot.send_message(message.chat.id, "Доступ пользователю открыт")
            return
        except:
            trainer_bot.send_message(message.chat.id, "Что-то пошло не так")
            return
    
@trainer_bot.message_handler(func=lambda message: True)
def func(message):
    user = check_user_by_id(message.chat.id)
    if user is not None:
        # тут будет логика, если нужна для приема если пользователь есть
        trainer_bot.send_message(message.chat.id, f"Я вас не понимаю")
        return
    user = check_user_by_token(message.text, message.chat.id)
    if user is None:
        trainer_bot.send_message(message.chat.id, f"Неверный токен")
        return
    else:
        trainer_bot.send_message(message.chat.id, f"{user.first_name}, Теперь у тебя есть власть давать подписки по команде /sub_add и проверять список подписок по команде /sub_check")
        return
