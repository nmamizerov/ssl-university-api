import re
from rest_framework.pagination import PageNumberPagination


class ApplicationPagination(PageNumberPagination):
    page_size_query_param = 'page_size'

    def get_next_link(self, **kwargs):
        return self.relative_path(super().get_next_link(**kwargs))

    def get_previous_link(self, **kwargs):
        return self.relative_path(super().get_previous_link(**kwargs))

    def relative_path(self, path):
        if path:
            return re.split('/api/|/api_admin/',  path)[1]
        else:
            return
