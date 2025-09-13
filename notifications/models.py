from comment_requests.models import CommentRequest
from places.models import PlaceUser
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


NOTIFICATION_TYPE_CHOICES = [
  ('user_comment', 'Комментарий пользователя'),
  ('admin_comment', 'Комментарий админа'),
]


class Notification(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="from_me_motifications", null=True, blank=True)
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="my_notifications", null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    answer = models.ForeignKey(PlaceUser, on_delete=models.CASCADE, blank=True, null=True)
    comment_request = models.ForeignKey(CommentRequest, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True)
    type = models.CharField(choices=NOTIFICATION_TYPE_CHOICES, max_length=200, default='user_comment')
    score = models.IntegerField(default=0)

    def create(self, from_user, to_user, object, text, type):
        notification = None
        if type == 'admin_comment':
            notification = Notification(from_user=from_user, to_user=to_user, comment_request=object, text=text)
        if type == 'user_comment':
            notification = Notification(from_user=from_user, to_user=to_user, answer=object, text=text)
            
        notification.type = type
        notification.save()
        # add websocket
        return notification
