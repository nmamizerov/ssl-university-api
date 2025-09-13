from datetime import datetime, timedelta

from django.db import models
from django.contrib.auth.models import AbstractUser


STATES = {
    'Регистрация': -2,
    'Создание персонажа': -1,
    'Онбординг': 0,
    'Прохождение урока': 1,
}
STATES_CHOICES = [(value, key) for key, value in STATES.items()]


class User(AbstractUser):
    rating_tournament = models.IntegerField(default=0)
    creation_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    male = models.BooleanField(null=True, blank=True)
    vip = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_admin_user = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='user_avatars', blank=True, null=True, default='user_avatars/default_avatar.png')
    email_confirmed = models.BooleanField(default=False)
    email_confirmation_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    balance = models.IntegerField(default=0)
    curr_simulator = models.IntegerField(default=0)
    send_notifications = models.BooleanField(default=True)
    last_notification = models.DateTimeField(null=True, blank=True)
    api_key = models.CharField(max_length=200, null=True, blank=True)
    utm = models.TextField(null=True, blank=True)
    last_action = models.IntegerField(choices=STATES_CHOICES, default=-2)
    last_action_time = models.DateTimeField(blank=True, null=True)
    last_lesson = models.ForeignKey('lessons.Lesson', on_delete=models.SET_NULL, blank=True, null=True)
    rating = models.IntegerField(default=1200)
    rating_fast = models.IntegerField(default=1200)
    rating_text_game = models.IntegerField(default=1200)
    subscribe = models.BooleanField(default=True)
    member = models.ForeignKey("club.Club", verbose_name="Клуб", on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey("company.Company", verbose_name="Компания", on_delete=models.SET_NULL, null=True, blank=True)
    company_admin = models.BooleanField(default=False)
    temporary_code = models.CharField(max_length=8, null=True, blank=True, unique=True)  
    tg_trainer_code = models.CharField(max_length=32, null=True, blank=True, unique=True) 
    tg_trainer_chat_id = models.BigIntegerField(null=True, blank=True)    
    facebook_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    vk_id = models.CharField(max_length=255, null=True, blank=True, unique=True)

    def write_history(self, value, lesson):
        self.balance += value

        histories = UserDayHistory.objects.filter(user=self, day=datetime.now())
        if histories.exists():
            history = histories.first()
            history.balance += value
            history.save()
        else:
            new_history = UserDayHistory(user=self, balance=value)
            new_history.save()

        self.last_action = STATES['Прохождение урока']
        self.last_action_time = datetime.now()
        self.last_lesson = lesson
        self.save()

    def __str__(self):
        return f"{self.email} {self.first_name} {self.last_name}"


class AuthAttempt(models.Model):
    key = models.CharField(max_length=500, null=True, blank=True)
    TYPES = (
        (0, 'Начало авторизации'),
        (1, 'Ошибка авторизации'),
        (2, 'Отказ от авторизации'),
        (3, 'Успех авторизации'),
    )
    status = models.IntegerField(default=0, choices=TYPES)
    code = models.CharField(max_length=255, blank=True, null=True, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    creation_time = models.DateTimeField(auto_now_add=True, blank=True)
    simulator = models.ForeignKey('simulators.Simulator', on_delete=models.CASCADE, null=True, blank=True)


class UserDayHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    day = models.DateField(auto_now_add=True)
    balance = models.IntegerField(blank=True, default=0)
