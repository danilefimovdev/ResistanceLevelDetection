import datetime


def convert_date_into_utc(date_string: str, forward: bool = False):

    date_object = datetime.datetime.fromisoformat(date_string)

    # Устанавливаем временную зону UTC+3
    utc_plus_3 = datetime.timezone(datetime.timedelta(hours=3))
    date_object_utc_plus_3 = date_object.replace(tzinfo=utc_plus_3)

    # Преобразовываем в UTC
    date_object_utc = date_object_utc_plus_3.astimezone(datetime.timezone.utc)

    if forward:
        minute_delta = datetime.timedelta(minutes=200)
        date_object_utc = date_object + minute_delta

    return date_object_utc.isoformat()
