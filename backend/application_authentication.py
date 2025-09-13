import logging
from knox.auth import TokenAuthentication
from django.utils import timezone
logger = logging.getLogger("django.server")




class ApplicationAuthentication(TokenAuthentication):
    def authenticate(self, request):
        result = super(ApplicationAuthentication, self).authenticate(request)
        return result