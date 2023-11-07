import random
import re
import string
from time import time

from django.db import connection
from django.utils import timezone


def timeit(func):
    def wrapper(*args):
        start = time()
        result = func(*args)
        end = time()
        print(f"{func.__name__}(): Execution time: {end - start:2f} s")
        return result

    return wrapper


def generate_barcode(record_type, counter):
    barcode = timezone.now().strftime("%y") + record_type
    barcode += "0" * (6 - len(counter)) + counter
    return barcode


def get_random_name(len=10):
    """Generate a random string of a given length."""
    return "".join(
        random.SystemRandom().choice(string.ascii_lowercase + string.digits)
        for _ in range(len)
    )


def print_sql_queries(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            for i, query in enumerate(connection.queries):
                sql = re.split(
                    r"(SELECT|FROM|WHERE|GROUP BY|ORDER BY|INNER JOIN|LIMIT)",
                    query["sql"],
                )
                if not sql[0]:
                    sql = sql[1:]
                sql = [(" " if i % 2 else "") + x for i, x in enumerate(sql)]
                print(
                    "\n### {} ({} seconds)\n\n{};\n".format(
                        i, query["time"], "\n".join(sql)
                    )
                )

    return wrapper


def get_date_range(start, end, format):
    now = timezone.now()

    try:
        start = (
            timezone.datetime.strptime(start, format) if type(start) is str else start
        )
    except ValueError:
        start = now
    finally:
        start = start.replace(hour=0, minute=0)

    try:
        end = timezone.datetime.strptime(end, format) if type(end) is str else end
    except ValueError:
        end = now
    finally:
        end = end.replace(hour=23, minute=59)

    if start > end:
        start = end.replace(hour=0, minute=0)

    return (start, end)


def is_iterable(obj):
    answer = True
    try:
        _ = iter(obj)
    except TypeError:
        answer = False
    return answer


def retrieve_group_items(request, queryset):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    this_lab_group = User.objects.all().filter(pi__in=[request.user.pi])
    if is_iterable(this_lab_group):
        queryset = queryset.filter(user__in=this_lab_group)
    else:
        assert isinstance(this_lab_group, User)
        queryset = queryset.filter(user=this_lab_group)
    return queryset
