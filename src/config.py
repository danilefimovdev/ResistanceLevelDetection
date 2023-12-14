import datetime
import os

API_KEY = os.environ.get('API_KEY')
API_SECRET = os.getenv("SECRET_KEY")

current_dir = os.path.dirname(__file__)
ALERT_PATH = os.path.join(current_dir, '..', 'static', 'alert.csv')
RESULT_PATH = os.path.join(current_dir, '..', 'static',
                           f'result_{datetime.datetime.now().strftime("%Y_%m_%dT%H_%M_%S")}.csv')
ALLOWED_PRICE_DIFF_TO_RESET_MAX_1 = 0.1
ALLOWED_PRICE_DIFF_TO_SET_MAX_2 = 0.06  # величина процента между ценами максимумов,
# чтобы считать их одним уровнем сопротивления
