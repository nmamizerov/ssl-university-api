from backend.application_viewset import AdminApplicationViewSet, ApplicationReadOnlyViewSet
from comment_requests.permissions import CommentRequestPermissions
from notifications.models import Notification
from pages.models import UserPageProgress
from places.models import PlaceUser
from .serializers import CommentRequestSerializer, AdminCommentRequestSerializer
from rest_framework import mixins
from .models import CommentRequest
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger("django.server")


class AdminCommentRequestViewSet(AdminApplicationViewSet):
    serializer_class = AdminCommentRequestSerializer
    permission_classes = [CommentRequestPermissions]

    def get_queryset(self):
        queryset = []
        if "simulator" in self.params:
            queryset = CommentRequest.objects.filter(place__page__lesson__simulator__id=self.params['simulator'], commented=False)
        else:
            queryset = CommentRequest.objects.all()
        return queryset

    @action(detail=True, methods=['POST'])
    def score(self, request, *args, **kwargs):
        comment = self.get_object()
        if not 'comment' in request.data:
            return Response({"comment": "Это обязательно"}, status=status.HTTP_400_BAD_REQUEST)
        comment.comment = request.data['comment']
        comment.commented = True
        comment.save()

        place_user = PlaceUser.objects.get(user=comment.user, place=comment.place)

        notification = Notification(from_user=request.user,
                                    to_user=comment.user,
                                    answer=place_user,
                                    comment_request=comment,
                                    text=request.data['comment'],
                                    type='admin_comment')
        notification.save()

        if comment.place.type == 'openquestionexpert' and comment.place.block_complete:
            current_place, user = comment.place, comment.user
            page_user = UserPageProgress.objects.get(page=current_place.page, user=user)

            if not current_place.award:
                award = 0
            user.write_history(value=award, lesson=current_place.page.lesson)

            place_user.is_completed = True
            place_user.save()

            for idx, place in enumerate(page_user.places):
                if current_place.id == int(place['id']):
                    page_user.places[idx]['complete'] = True
            page_user.save()

            current_place.finish_complete(user, current_place.page.lesson.simulator, page_user)

        return Response()


class CommentRequestViewSet(ApplicationReadOnlyViewSet, mixins.CreateModelMixin):
    pagination_class = None
    serializer_class = CommentRequestSerializer
    queryset = CommentRequest.objects.all()
