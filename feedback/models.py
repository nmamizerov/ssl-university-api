from django.db import models
from django.contrib.auth import get_user_model
import random
User = get_user_model()


FIRST_PART = ['Я-эмоция', 'Я-ощущение', 'Я-эмоция/Я-ощущение', 'Факт', 'Потребность', 'Факт/потребность' ]
LAST_PART = ['Открытый вопрос', 'Закрытый вопрос', 'Право на отказ/эмоцию/границу', 'Просьба', 'Требования']

def rand_slug():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))

# Create your models here.
class Game(models.Model):
    code = models.CharField(max_length=10, unique=True, default=rand_slug)
    is_started = models.BooleanField(default=False)
    is_end =  models.BooleanField(default=False)
    round = models.IntegerField(default = 0)
    situation = models.TextField(blank = True)
    def __str__(self):
        return f"{self.code}"

class GameRound(models.Model):
    seq_no = models.IntegerField()
    structure = models.TextField(blank = True)
    cards_sends = models.IntegerField(default = 0)

class Gameuser(models.Model):
    game = models.ForeignKey("Game", on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    card1 = models.CharField(max_length=100, blank =True)
    card2 = models.CharField(max_length=100, blank =True)
    card3 = models.CharField(max_length=100, blank =True)
    lifes = models.IntegerField(default = 3)
class GameRoundCard(models.Model):
    round = models.ForeignKey("GameRound", on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey("Gameuser", on_delete=models.SET_NULL, null=True, blank=True)
    card = models.TextField()

class FeedbackSituation(models.Model):
    text = models.TextField(blank = True, null = True)
    phrase = models.TextField(blank = True, null = True)
    def __str__(self):
        return f"{self.text}"


class FeedbackSituationUser(models.Model):
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)
    situation = models.ForeignKey('FeedbackSituation', verbose_name="Ситуация", on_delete=models.CASCADE)
    answer = models.TextField(blank = True, null = True)
    structure = models.TextField(blank = True, null = True)
    marks = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    my_count_marks = models.IntegerField(default=0)
    def __str__(self):
        return f"{self.situation.text}"
    def add_structure(self):
        count = 3 
        rnd_data = random.randint(1, 5)
        if rnd_data == 1:
            count = 2
        if rnd_data == 5: 
            count = 4
        structure = ' + '.join(random.choices(FIRST_PART, k=3))
        rnd_data = random.randint(1, 8)
        if rnd_data != 1:
            structure += f" + {random.choice(LAST_PART)}"
        self.structure = structure
        self.save()
        
class FeedbackSituationUserMark(models.Model):
    s_user = models.ForeignKey("FeedbackSituationUser", verbose_name="Пользователь", on_delete=models.CASCADE)
    mark = models.IntegerField(default = 0)
    comment = models.TextField(blank = True, null = True)