from places.models import Place
from django.db import models
import logging
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger("django.server")


class CommentRequest(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    commented = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} (user={})'.format(self.place, self.user)
