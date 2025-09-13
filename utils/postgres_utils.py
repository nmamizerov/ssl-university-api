from django.db import connection


def disable_seqscan():
    with connection.cursor() as c:
        c.execute('SET enable_seqscan = OFF')