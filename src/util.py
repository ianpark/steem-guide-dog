from datetime import datetime
from pytz import timezone

KR = timezone('Asia/Seoul')

def get_kr_time(ts):
    return datetime.fromtimestamp(ts, KR)

def get_kr_time_from_timestamp(ts):
    return get_kr_time(ts).strftime('%Y년 %-m월 %-d일')
    