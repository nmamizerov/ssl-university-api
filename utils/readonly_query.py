from django.db.models.query import QuerySet, NamedValuesListIterable


class RowsIterable(NamedValuesListIterable):

    def __iter__(self):
        queryset = self.queryset
        query = queryset.query
        compiler = query.get_compiler(queryset.db)
        values_select = query.values_select or [f.attname for f in queryset.model._meta.concrete_fields]
        names = [
            *query.extra_select,
            *values_select,
            *query.annotation_select
        ]
        tuple_class = self.create_namedtuple_class(*names)
        new = tuple.__new__
        for row in compiler.results_iter(chunked_fetch=self.chunked_fetch, chunk_size=self.chunk_size):
            yield new(tuple_class, row)


class ReadonlyQuerySet(QuerySet):

    def __init__(self, *args, **kwargs):
        super(ReadonlyQuerySet, self).__init__(*args, **kwargs)
        self._iterable_class = RowsIterable

    def _insert(self, *args, **kwargs):
        raise Exception("Readonly")

    def _batched_insert(self, *args, **kwargs):
        raise Exception("Readonly")

    def create(self, *args, **kwargs):
        raise Exception("Readonly")

    def bulk_create(self, *args, **kwargs):
        raise Exception("Readonly")

    def update(self, *args, **kwargs):
        raise Exception("Readonly")

    def _update(self, *args, **kwargs):
        raise Exception("Readonly")

    def bulk_update(self,  *args, **kwargs):
        raise Exception("Readonly")

    def delete(self,  *args, **kwargs):
        raise Exception("Readonly")