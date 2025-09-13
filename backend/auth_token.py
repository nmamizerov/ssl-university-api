import logging

from knox.views import LoginView as KnoxLoginView
from rest_framework.authentication import BaseAuthentication
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework import status

from django.contrib.auth import get_user_model
from user_profile.models import AuthAttempt
from utils.audit.views import LoggingMixin

logger = logging.getLogger("django.server")
audit = logging.getLogger('audit')
User = get_user_model()


class ParamsAuthentication(BaseAuthentication):
    def authenticate(self, request):
        serializer = AuthTokenSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return (user, None)

from rest_framework import serializers
class TokenSerializer(serializers.Serializer):
    token = serializers.CharField()
    expiry = serializers.DateTimeField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    admin = serializers.BooleanField()


from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
@method_decorator(name='post', decorator=swagger_auto_schema(
    request_body=AuthTokenSerializer,
    security=[],
    responses={status.HTTP_200_OK: TokenSerializer}
))
class AuthToken(LoggingMixin, KnoxLoginView):
    authentication_classes = [ParamsAuthentication]
    serializer_class = TokenSerializer

    def get_post_response_data(self, request, token, instance):
        user = request.user
        audit.info({'event': 'authorize', 'status': 'success'}, extra=dict(user=user))
        instance.expiry = None
        instance.save()
        return {
            'token': token,
            'email': user.email,
            'full_name': f"{user.first_name} {user.last_name}",
            'admin': user.is_superuser
        }
