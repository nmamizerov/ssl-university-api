from django.db import models
from user_profile.models import User
from simulators.models import Simulator
import random
import string

# Create your models here.
def rand_slug():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))

class Certificate(models.Model):
    slug = models.CharField(max_length=6, unique=True, default=rand_slug)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    simulator = models.ForeignKey(Simulator, on_delete=models.CASCADE)
    creation_time = models.DateTimeField(auto_now_add=True, blank=True)
    image = models.ImageField(upload_to='certificates', blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['slug', ]),
        ]

    def __str__(self):
        return '{} {}'.format(str(self.user), self.simulator)