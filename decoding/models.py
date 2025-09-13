from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.
class Situation(models.Model):
    text = models.TextField(blank = True, null = True)
    phrase = models.TextField(blank = True, null = True)
    answer = models.TextField(blank = True, null = True)
    points = models.IntegerField(default=0)
    def __str__(self):
        return f"{self.text}"

class SituationUser(models.Model):
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)
    situation = models.ForeignKey('Situation', verbose_name="Ситуация", on_delete=models.CASCADE)
    answer = models.TextField(blank = True, null = True)
    points = models.IntegerField(default=0)
    marks = models.IntegerField(default=0)
    my_count_marks = models.IntegerField(default=0)
    def __str__(self):
        return f"{self.situation.text}"

class SituationUserMark(models.Model):
    s_user = models.ForeignKey("SituationUser", verbose_name="Пользователь", on_delete=models.CASCADE)
    mark_id = models.IntegerField(default = 0)

class userDecoding(models.Model):
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    def __str__(self):
        return f"{self.user.first_name}"