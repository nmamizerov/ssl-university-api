from datetime import datetime
import logging
import socket
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings


class ELKFormatter(logging.Formatter):

    def format(self, record):
        assert isinstance(record.msg, dict)

        user = record.__dict__.get('user')
        message = record.msg.copy()
        data = dict(
            event=message.pop('event', ''),
            eventdate=datetime.utcnow().isoformat(timespec='seconds'),
            host=dict(
                name=socket.gethostname(),
                ip=socket.gethostbyname(socket.gethostname())
            ),
            subsystem=settings.APP_NAME,
            format_version=1,
            username=(user.username if user else None),
            **message
        )

        return json.dumps(data, cls=DjangoJSONEncoder, ensure_ascii=False)
