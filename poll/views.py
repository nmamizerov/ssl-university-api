from django.shortcuts import render
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from django.core.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.http import HttpResponse
from .models import botUser, Survey, botUserSurvey
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import string
# import logging
# logging.basicConfig(filename='example.log', level=logging.DEBUG)
# Create your views here.


TOKEN = '5677288856:AAEFERquQNcE9iatXHRxNogvn7tDrAUWWwc'
bot = telebot.TeleBot(TOKEN, threaded=False, parse_mode='HTML')
def user_exists(chat_id):
    tg = botUser.objects.filter(chat_id=chat_id).first()
    if tg is not None: 
        return tg
    else: 
        return None

def rand_slug():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))

class PollBot(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        if request.META['CONTENT_TYPE'] == 'application/json':
    
            json_data = request.body.decode('utf-8')
            update = telebot.types.Update.de_json(json_data)
            bot.process_new_updates([update])

            return HttpResponse("")

        else:
            raise PermissionDenied

@bot.message_handler(commands=['start'])
def get_okn(message):
    code = None
    try:
        command, code =  message.text.split(' ')
    except Exception as e:
        pass
    user = user_exists(message.chat.id)
    if user is not None:
        if code is not None: 
            user.company_slug = code
            user.save()
        if user.age is None: 
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text="<18", callback_data="age?0"),InlineKeyboardButton(text="18-24", callback_data="age?1")],
                [InlineKeyboardButton(text="25-34", callback_data="age?2"),InlineKeyboardButton(text="35-45", callback_data="age?3")],
                [InlineKeyboardButton(text=">45", callback_data="age?4")]
            ])
            bot.send_message(message.chat.id, """Добро пожаловать в опросы от soft skills lab!
Здесь Вы сможете пройти тесты эмоционального и социального интеллектов, узнать тип корпоративной культуры в вашей компании.
Чтобы продолжить выберите ваш <b>возраст</b>
""", reply_markup=reply_markup)
            
            return
        if user.sex is None:
            reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(text="Мужской", callback_data="sex?1"),InlineKeyboardButton(text="Женский", callback_data="sex?0")],
            ])
            bot.send_message(message.chat.id, 'Выберите ваш пол', reply_markup=reply_markup)
            return
        survey = Survey.objects.filter(is_main = True).first()
        u_survey = botUserSurvey.objects.filter(survey=survey, bot_user = user).first()
        if u_survey.finished:
            bot.send_message(message.chat.id, "Вы можете проходить какие-то другие опросы")
        else: 
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text="Начать тест", url=f"https://skillslab.center/poll/{survey.slug}/{u_survey.slug}")]
            ])
            bot.send_message(message.chat.id, 'Добро пожаловать в опросы Soft Skills Lab. Чтобы продолжить, пройдите основной тест', reply_markup=reply_markup) 
        
    else: 
        user = botUser.objects.create(
            chat_id = message.chat.id
        )
        if code is None: 
            code = rand_slug()
        user.company_slug = code
        user.save()
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(text="<18", callback_data="age?0"),InlineKeyboardButton(text="18-24", callback_data="age?1")],
            [InlineKeyboardButton(text="25-34", callback_data="age?2"),InlineKeyboardButton(text="35-45", callback_data="age?3")],
            [InlineKeyboardButton(text=">45", callback_data="age?4")]
        ])
        bot.send_message(message.chat.id, """Добро пожаловать в опросы от soft skills lab!
Здесь Вы сможете пройти тесты эмоционального и социального интеллектов, узнать тип корпоративной культуры в вашей компании.
Чтобы продолжить выберите ваш <b>возраст</b>
""", reply_markup=reply_markup)


@bot.callback_query_handler(func=lambda call: True)
def soution(inline_query):
    user = user_exists(inline_query.message.chat.id)
    try:
        key, command = inline_query.data.split('?', 1)
    except: 
        pass
    if key == 'age': 
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(text="Мужской", callback_data="sex?1"),InlineKeyboardButton(text="Женский", callback_data="sex?0")],
        ])
        user.age = command
        user.save()
        bot.edit_message_text('Выберите ваш пол', inline_query.message.chat.id, inline_query.message.id, reply_markup=reply_markup)
        return
    if key == 'sex': 
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(text="Мужской", callback_data="sex?1"),InlineKeyboardButton(text="Женский", callback_data="sex?0")],
        ])
        user.sex = command
        user.save()
        survey = Survey.objects.filter(is_main = True).first()
        u_survey = botUserSurvey.objects.filter(survey=survey, bot_user = user).first()
        if u_survey is None: 
            s_slug = rand_slug()
            u_survey = botUserSurvey.objects.create(
                survey = survey, 
                bot_user = user, 
                slug = s_slug
            )
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(text="Начать тест", url=f"https://skillslab.center/poll/{survey.slug}/{u_survey.slug}")]
        ])
        bot.edit_message_text('Теперь мы можем начать.', inline_query.message.chat.id, inline_query.message.id, reply_markup=reply_markup)
        return

    