from django.db import models
from django.contrib.auth import get_user_model
import random
User = get_user_model()


FIRST_PART = ['Я-эмоция', 'Я-ощущение', 'Я-эмоция/Я-ощущение', 'Факт', 'Потребность', 'Факт/потребность' ]
LAST_PART = ['Открытый вопрос', 'Закрытый вопрос', 'Право на отказ/эмоцию/границу', 'Просьба', 'Требования']

def rand_slug():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))

# Create your models here.

class FeedbackSituation(models.Model):
    text = models.TextField(blank = True, null = True)
    phrase = models.TextField(blank = True, null = True)
    def __str__(self):
        return f"{self.text}"


class FeedbackSituationUser(models.Model):
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE, related_name="user_decomosition")
    situation = models.ForeignKey('FeedbackSituation', verbose_name="Ситуация", on_delete=models.CASCADE)
    answer = models.TextField(blank = True, null = True)
    marks = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    my_count_marks = models.IntegerField(default=0)
    def __str__(self):
        return f"{self.situation.text}"
        
class FeedbackSituationUserMark(models.Model):
    s_user = models.ForeignKey("FeedbackSituationUser", verbose_name="Пользователь", on_delete=models.CASCADE)
    mark = models.IntegerField(default = 0)
    comment = models.TextField(blank = True, null = True)