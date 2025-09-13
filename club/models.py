from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
# Create your models here.
class Club(models.Model):
    name = models.CharField(max_length=50)
    price = models.CharField(max_length=50)
    description = models.TextField()
    schedule = models.CharField(max_length=200)
    link = models.CharField(max_length=50)
    show = models.BooleanField(default=True)
    img = models.ImageField(upload_to='clubs', blank=True, null=True)
    def __str__(self):
        return self.name

class Tournament(models.Model): 
    name = models.CharField(max_length=50)
    description = models.TextField()
    schedule = models.CharField(max_length=200)
    link = models.CharField(max_length=50)
    show = models.BooleanField(default=True)
    img = models.ImageField(upload_to='clubs', blank=True, null=True)
    place1 = models.ForeignKey(User, verbose_name="место 1", on_delete=models.CASCADE, blank=True, null=True)
    place2 = models.ForeignKey(User, verbose_name="место 2", on_delete=models.CASCADE, related_name="place2", blank=True, null=True)
    place3 = models.ForeignKey(User, verbose_name="место 3", on_delete=models.CASCADE, related_name="place3", blank=True, null=True)
    def __str__(self):
        return self.name

class Player(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    img = models.ImageField(upload_to='clubs', blank=True, null=True)
    order = models.IntegerField(verbose_name="порядок вывода. Чем больше тем раньше")
    def __str__(self):
        return self.name


class Game(models.Model):
    TYPES = (
        (0, 'Конфликты'),
        (1, 'Переговоры')
    )
    player1 = models.ForeignKey(User, verbose_name="игрок 1", on_delete=models.CASCADE)
    player2 = models.ForeignKey(User, verbose_name="игрок 2", on_delete=models.CASCADE, related_name="player2_game")
    score1 = models.IntegerField()
    score2 = models.IntegerField()
    judges = models.IntegerField(verbose_name="судей")
    type = models.IntegerField(verbose_name="тип", choices=TYPES)
    is_elo = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True, blank=True)
    def __str__(self):
        return f"{self.player1.last_name} {self.score1}:{self.score2} {self.player2.last_name}"