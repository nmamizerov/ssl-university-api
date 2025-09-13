from datetime import timedelta, datetime, timezone
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class note(models.Model):
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)
    text = models.TextField(blank = True, null = True)
    title = models.TextField(blank=True, null = True)
    tags = models.ManyToManyField("tag", verbose_name="теги", blank = True)
    def __str__(self):
        return f"{self.user.email}"

class tag(models.Model):
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    def __str__(self):
        return f"{self.name}"

