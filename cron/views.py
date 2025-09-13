from django_cron import CronJobBase, Schedule

from cron.models import CronLog
from club.models import Game
from subscriptions.models import Subscription, UserSubscription
from bot.models import tgSend
from django.db.models import Q
import math
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
TOKEN = '5362028988:AAFNicUn5owN_OGq-JwdaTTG1g60eRtDlcM'
bot = telebot.TeleBot(TOKEN, threaded=False)



class CronJobsSubscriptions(CronJobBase):
    RUN_EVERY_MINUTES = 10

    schedule = Schedule(run_every_mins=RUN_EVERY_MINUTES)
    code = 'cron.subscriptions'

    def do(self):
        user_subscriptions = UserSubscription.objects.filter(type__gte=5)

        for user_subscription in user_subscriptions:
            try:
                user_subscription.charge()
            except ValueError as error:
                CronLog.objects.create(
                    # TODO: cron=self
                    title=str(user_subscription),
                    text=str(error),
                    user=user_subscription.user
                )
                user_subscription.rebill_ID = None
                user_subscription.type = 2
                user_subscription.resubscribe = False
                user_subscription.alert = False
                user_subscription.save()
                user_subscription.subscription.send_email(type = 2, user = user_subscription.user)

class CronJobsGames(CronJobBase):
    RUN_EVERY_MINUTES = 5

    schedule = Schedule(run_every_mins=RUN_EVERY_MINUTES)
    code = 'cron.games'

    def do(self):
        games = Game.objects.filter(is_elo=False).order_by('date')
        K = 30
        for game in games:
            if game.type == 0:
                # конфликты
                prob1 = 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (game.player2.rating_fast - game.player1.rating_fast) / 400))
                prob2 = 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (game.player1.rating_fast - game.player2.rating_fast) / 400))
                game.player1.rating_fast = game.player1.rating_fast + K * (game.score1/game.judges - prob1)
                game.player2.rating_fast = game.player2.rating_fast + K * (game.score2/game.judges - prob2)
                game.player1.save()
                game.player2.save()
                game.is_elo = True
                game.save()
            else: 
                # переговоры
                prob1 = 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (game.player1.rating - game.player2.rating) / 400))
                prob2 = 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (game.player2.rating - game.player1.rating) / 400))
                game.player1.rating = game.player1.rating + K * (game.score1/game.judges - prob1)
                game.player2.rating = game.player2.rating + K * (game.score2/game.judges - prob2)
                game.player1.save()
                game.player2.save()
                game.is_elo = True
                game.save()

class CronJobsTG(CronJobBase):
    RUN_EVERY_MINUTES = 5

    schedule = Schedule(run_every_mins=RUN_EVERY_MINUTES)
    code = 'cron.tg'

    def do(self):
        sends = tgSend.objects.all()[:30]
        for send in sends: 
            try: 
                bot.send_message(send.tg.chat_id, send.message, parse_mode="HTML", disable_web_page_preview=True)
                send.delete()
            except:
                send.tg.active = False
                send.tg.save()
