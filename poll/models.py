from django.db import models
from django.contrib.auth import get_user_model
import random
import string
User = get_user_model()
def rand_slug():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))

STATUS = (
    (1, 'Plus'),
    (-1, 'Minus'),
)
CATEGORY = (
    ( 0, 'самого пользователя'),
    ( 1, 'друзья и родственники'),
    ( 2, 'Работа')
)
AGE = (
    (0, 'Меньше 18'),
    (1, '18-24'),
    (2, '25-34'),
    (3, '35-45'),
    (4, 'больше 45')
)
SEX = (
    (0, 'W'),
    (1, 'M')
)
# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    def __str__(self):
        return self.name
class Result(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True, blank=True)
    max_points = models.IntegerField(default = 100)
    min_points = models.IntegerField(default = 0)
    bad_points = models.IntegerField(default = 0)
    normal_points = models.IntegerField(default = 0)
    good_points = models.IntegerField(default = 0)
    bad_comment = models.TextField(blank=True)
    normal_comment = models.TextField(blank=True)
    good_comment = models.TextField(blank=True)
    def __str__(self):
        return self.name
class Question(models.Model):
    name = models.TextField(blank = True, null = True)
    result = models.ManyToManyField('Result',  null=True, blank=True)
    type = models.IntegerField(choices=STATUS, default=-1)
    default_answers = models.BooleanField(default=True)
    def __str__(self):
        return self.name
class Survey(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    results = models.ManyToManyField(Result, blank=True)
    category = models.IntegerField(choices=CATEGORY, default=0)
    questions = models.ManyToManyField(Question, through='Survey_Question')  
    parent = models.ForeignKey("self", blank=True, on_delete=models.SET_NULL, null=True)
    slug = models.CharField(max_length=255, verbose_name='slug')
    is_main = models.BooleanField(default=False)
    
class Survey_Question(models.Model):
    survey = models.ForeignKey('Survey', on_delete=models.CASCADE, null=True, blank=True)
    question = models.ForeignKey('Question', on_delete=models.CASCADE, null=True, blank=True)
    order = models.IntegerField(default=0)
    page = models.IntegerField(default=1)

class Answer(models.Model):
    name = models.TextField(blank = True, null = True)
    question = models.ForeignKey('Question', on_delete=models.CASCADE, null=True, blank=True)
    value = models.IntegerField(default = 1)

    
class botUser(models.Model):
    chat_id = models.BigIntegerField()
    command = models.TextField(blank = True, null = True)
    value = models.TextField(blank=True, null = True)
    slug = models.CharField(max_length=255, verbose_name='slug')
    age = models.IntegerField(blank=True, null = True, choices=AGE)
    sex = models.IntegerField(blank=True, null = True, choices=SEX)
    company_slug = models.TextField(blank=True, null = True)

class botUserSurvey(models.Model):
    survey = models.ForeignKey('Survey', on_delete=models.CASCADE, null=True, blank=True)
    bot_user = models.ForeignKey('botUser', on_delete=models.CASCADE, null=True, blank=True)
    slug = models.CharField(max_length=255, verbose_name='slug')
    finished =  models.BooleanField(default=False)
    page = models.IntegerField(default = 1)

class botUserSurveyResult(models.Model):
    bot_user_survey= models.ForeignKey('botUserSurvey', on_delete=models.CASCADE, null=True, blank=True)
    result = models.IntegerField(default=0)

class botUserSurveyQuestion(models.Model):
    bot_user_survey= models.ForeignKey('botUserSurvey', on_delete=models.CASCADE, null=True, blank=True)
    answer = models.CharField(max_length=255, verbose_name='slug')