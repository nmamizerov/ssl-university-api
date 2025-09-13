from datetime import timedelta, datetime, timezone

from django.db import models
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from emails.models import Email

User = get_user_model()

class tgUser(models.Model):
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    chat_id = models.BigIntegerField()
    command = models.TextField(blank = True, null = True)
    value = models.TextField(blank=True, null = True)
    def __str__(self):
        return f"{self.user.email}"

class AITg(models.Model):
    chat_id = models.BigIntegerField()
    value = models.TextField(blank=True, null = True)
    def __str__(self):
        return f"{self.chat_id}"        

class tgSend(models.Model):
    tg = models.ForeignKey(tgUser, on_delete=models.CASCADE)
    message = models.TextField()

