import json
import logging

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)



def stringify(value):
    try:
        return json.dumps(value, cls=DjangoJSONEncoder, ensure_ascii=False)
    except Exception:
        return str(value)


class LoggingMixin:

    CLEANED_SUBSTITUTE = "********************"

    SENSITIVE_FIELDS = frozenset((
        "api",
        "key",
        "pass",
        "token",
        "secret",
        "password",
        "signature",
    ))

    def initial(self, request, *args, **kwargs):
        self.log = dict()
        self._initialized_at = timezone.now()
        super(LoggingMixin, self).initial(request, *args, **kwargs)

    def handle_exception(self, exc):
        response = super(LoggingMixin, self).handle_exception(exc)
        if isinstance(exc, APIException):
            self.log["errors"] = stringify(exc.get_full_details())
        else:
            self.log["errors"] = stringify(exc)
        return response

    def finalize_response(self, request, response, *args, **kwargs):
        response = super(LoggingMixin, self).finalize_response(
            request, response, *args, **kwargs
        )
        if self.should_log(request, response):
            try:
                kwargs.pop('format', None)
                self.log.update(kwargs)
                self.log.update(
                    {
                        'request': {
                            'query_params': stringify(self._get_query_params(request)),
                            'payload':  stringify(self._get_request_data(request))
                        },
                        'event': self._get_action_name(request),
                        'status': self._get_status(response),
                        'status_code': response.status_code,
                        'response_ms': self._get_response_ms(),
                    }
                )
            except Exception:
                logger.warning(f"Error while logging {request.method} {request.get_full_path()}", exc_info=True)
        return response

    def should_log(self, request, response):
        return request.method != "GET"

    def _get_action(self, request):
        return self.action if hasattr(self, 'action') else self.request.method.lower()

    def _get_action_name(self, request):
        return f"{self.__class__.__module__}.{self.__class__.__name__}.{self._get_action(request)}"

    def _get_status(self, response):
        return 'success' if response.status_code < 400 else 'error'

    def _get_query_params(self, request):
        return self._clean_data(request.query_params.dict())

    def _get_request_data(self, request):
        try:
            data = request.data.dict()
        except AttributeError:
            data = request.data

        return self._clean_data(data)

    def _get_response_ms(self):
        td = timezone.now() - self._initialized_at
        response_ms = int(td.total_seconds() * 1000)
        return max(response_ms, 0)

    def _clean_data(self, data, whitelist=[], blacklist=[]):
        if isinstance(data, bytes):
            data = data.decode(errors="replace")

        if isinstance(data, list):
            return [self._clean_data(d) for d in data]
        if isinstance(data, dict):
            data = dict(data)

            sensitive_fields = self.SENSITIVE_FIELDS - set(whitelist)
            sensitive_fields = sensitive_fields | set(blacklist)

            for key, value in data.items():
                if key.lower() in sensitive_fields:
                    data[key] = self.CLEANED_SUBSTITUTE
                elif isinstance(value, list) or isinstance(value, dict):
                    data[key] = self._clean_data(value)

        return data


class ModelLoggingMixin:
    def perform_create(self, serializer):
        super(ModelLoggingMixin, self).perform_create(serializer)
        try:
            instance = getattr(serializer, 'instance', None)
            if hasattr(instance, 'pk'):
                self.log['pk'] = instance.pk
        except Exception:
            pass
