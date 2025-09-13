from django.utils.deprecation import MiddlewareMixin
from simulators.models import Simulator
import tldextract
import logging
logger = logging.getLogger("django.server")

class GetSimulator(MiddlewareMixin):
    def process_request(self, request):
        referer = request.headers.get('X-App-Name')
        if referer:
            extracted = tldextract.extract(referer)
            if (extracted.domain == "mysimulator"):
                host = "{}.{}.{}".format(extracted.subdomain, extracted.domain, extracted.suffix)
                simulator = Simulator.objects.filter(domain=host).first()
                request.simulator = simulator
            else:
                simulator = Simulator.objects.filter(alias=referer).first()
                request.simulator = simulator
        else:
            request.simulator = None
        return None