from datetime import datetime, timezone
import random
import string

import pytz


def datetime_now():
    return datetime.now(timezone.utc)

def random_string(N):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(N))