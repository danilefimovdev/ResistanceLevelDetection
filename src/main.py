import sys

import binance.exceptions
from binance.client import Client
from binance.enums import HistoricalKlinesType

from src.config import API_KEY, API_SECRET, ALERT_PATH, ALLOWED_PRICE_DIFF_TO_SET_MAX_2, \
    ALLOWED_PRICE_DIFF_TO_RESET_MAX_1, RESULT_PATH
from src.csv_utils import read_csv, write_csv, create_csv_result_file
from src.utils import convert_date_into_utc


client = Client(API_KEY, API_SECRET)


def get_strength_of_alert(resist_level_len: int) -> int:
    """
    Функция возвращает уровень сигнала (1, 2, 3). Чем больше значение, тем сильнее был сигнал
    :param resist_level_len: длина уровня сопротивления
    """

    if 0 < resist_level_len <= 50:
        return 1
    elif 50 < resist_level_len <= 100:
        return 2
    else:  # 100 < resist_level_len <= 150
        return 3


def get_historical_klines(symbol: str, end_str: str = None, profit: bool = False) -> list[float] | None:
    """
    Функция отправляет запрос на биржу с получением исторической информации по барам
    :param symbol: торговая пара
    :param end_str: время, от которого мы будем начинать смотреть бары
    :param profit: флаг, который задаст другой порядок свечей (используется при получении данных для
    нахождения максимального профита)
    """

    try:
        req_result = client.get_historical_klines(symbol=symbol,
                                                  interval=Client.KLINE_INTERVAL_1MINUTE,
                                                  limit=201,
                                                  end_str=end_str,
                                                  klines_type=HistoricalKlinesType.FUTURES)
    except binance.exceptions.BinanceAPIException:
        historical_klines = None
        print(f"!!!!!!!!!!!!!!!! - Ошибка с символом {symbol} - !!!!!!!!!!!!!!!!")
    # TODO: подумать как обработать биткоин памп, так как формат его записи отличается. Пока что будем пропускать
    else:
        if not profit:
            historical_klines = [float(item[2]) for item in req_result[-1:-154:-1]]
        else:
            historical_klines = [float(item[2]) for item in req_result]
    return historical_klines


def find_max_possible_profit(klines_data: list, alert_price: float) -> str:
    """
    Функция находит максимальный возможный профит от сигнала (в %)
    :param klines_data: список high цены полученных баров
    :param alert_price: величина цены сигнала
    """

    max_price = 0

    for kline_price in klines_data:
        if kline_price > max_price:
            max_price = kline_price

    max_profit = round(((max_price/alert_price)-1)*100, ndigits=3)
    return max_profit


def is_price_diff_allowed(kline_price: float, is_max_1_checked: bool, max_1: float) -> tuple[bool, bool]:
    """
    Функция проверяет допустима ли разница значения текущего зафиксированного максимума и нового значения для
    переназначения максмума
    :param kline_price: проверяемая цена
    :param is_max_1_checked: флаг, показывающий какому максимуму предполагается задать новое значение
    :param max_1: величина первого максимума (граница уровня сопротивления)
    """

    allowed_percentage_diff = ALLOWED_PRICE_DIFF_TO_RESET_MAX_1 if is_max_1_checked else ALLOWED_PRICE_DIFF_TO_SET_MAX_2
    kline_diff = abs((max_1-kline_price)/max_1*100) if not is_max_1_checked else (max_1-kline_price)/max_1*100

    if is_max_1_checked:
        if kline_diff > allowed_percentage_diff:
            is_allowed = True
            keep_iterate = False
        else:
            is_allowed = False
            keep_iterate = False
    else:
        if kline_diff <= allowed_percentage_diff:
            is_allowed = True
            keep_iterate = True
        elif allowed_percentage_diff < kline_diff < ALLOWED_PRICE_DIFF_TO_RESET_MAX_1:
            is_allowed = False
            keep_iterate = True
        else:
            is_allowed = False
            keep_iterate = False
    return is_allowed, keep_iterate


def get_analysis_result(is_alert_valid: bool, alert_datatime: str, alert_symbol: str, alert_price: float, id_: int,
                        max_1_bar_counter: int, max_2_bar_counter: int) -> list:
    """
    Функция
    :param is_alert_valid: флаг, указывающий на нахождение уровня сопротивления
    :param alert_datatime: время сигнала
    :param alert_symbol: торговая пара
    :param alert_price: величина цены сигнала
    :param id_: порядковый номер сигнала
    :param max_1_bar_counter: порядковый номер бара, составляющего уровень сопротивления (идем обратно от свечи сигнала)
    :param max_2_bar_counter: порядковый номер бара, составляющего уровень сопротивления (идем обратно от свечи сигнала)
    """

    if is_alert_valid:
        borders_count = 1
        resist_level_len = max_2_bar_counter - max_1_bar_counter + borders_count
        end_time_boundary = convert_date_into_utc(date_string=alert_datatime, forward=True)
        klines_data = get_historical_klines(symbol=alert_symbol, end_str=end_time_boundary, profit=True)
        result = [id_, True, get_strength_of_alert(resist_level_len=resist_level_len), resist_level_len,
                  max_1_bar_counter, max_2_bar_counter, alert_symbol,
                  find_max_possible_profit(klines_data=klines_data, alert_price=alert_price)]
    else:
        result = [id_, False, 0, 0, 0, 0, alert_symbol, 0]
    return result


def find_resistance_level(klines_data: list[float], alert_price: float) -> tuple:
    """
    Функция определяет, был ли пробит уровень сопротивления и на каких барах он существует
    :param klines_data: список high цены полученных баров
    :param alert_price: величина цены сигнала
    """

    max_1 = 0
    max_2 = 0
    max_1_bar_numb = 0
    max_2_bar_numb = 0

    current_kline_counter = -1

    for kline_price in klines_data[:151]:
        kline_price = float(kline_price)
        current_kline_counter += 1

        if current_kline_counter < 2:  # Только с третьего бара мы сможем получать максимумы (2 слева и 2 справа должны
            # быть ниже текущего бара, чтобы он считался максимумом).
            continue

        if kline_price > alert_price:  # В этом случае мы прекращаем поиски уровня. Он мог быть найден или отсутствовать
            break

        if all((kline_price >= float(klines_data[current_kline_counter+1]),
                kline_price >= float(klines_data[current_kline_counter+2]),
                kline_price >= float(klines_data[current_kline_counter-1]),
                kline_price >= float(klines_data[current_kline_counter-2]))):  # условие существования максимума.

            if not max_1 or (is_price_diff_allowed(kline_price=kline_price, is_max_1_checked=True, max_1=max_1)[0]
                             and max_2 == 0 and max_1 < kline_price):
                # перезаписываем 1-ый максимум и начинаем искать уровень от него, либо записывает первое значение max_1
                max_1 = kline_price
                max_1_bar_numb = current_kline_counter
            else:  # если величина максимума меньше, то мы проверяем на существование уровня сопротивления.
                is_allowed_to_set, keep_iterate = is_price_diff_allowed(kline_price=kline_price, is_max_1_checked=False,
                                                                        max_1=max_1)
                if is_allowed_to_set and keep_iterate:
                    max_2 = kline_price
                    max_2_bar_numb = current_kline_counter
                elif is_allowed_to_set is False and keep_iterate is True:
                    continue
                else:
                    break
    if max_2 == 0:  # значит, уровень сопротивления не был найден (не был найден второй максимум для утверждения
        # уровня на первом максимуме).
        is_alert_valid = False
        print('!!!!!!!!!!!!!!!! - По прохождению проверки уровень не был найден - !!!!!!!!!!!!!!!!')
    else:
        is_alert_valid = True
        resist_level_len = max_2_bar_numb-max_1_bar_numb + 1  # 1 - границы, которые тоже входят в уровень сопротивления
        print(f'!!!!!!!!!!!!!!!! - По прохождению проверки найден уровень, длинною {resist_level_len}. '
              f'Это от {max_1_bar_numb} до {max_2_bar_numb} бара - !!!!!!!!!!!!!!!!')

    return is_alert_valid, max_1_bar_numb, max_2_bar_numb


def main():

    create_csv_result_file(file_path=RESULT_PATH)
    file_reader = read_csv(ALERT_PATH)
    file_reader.__next__()

    note_list = []

    for row in file_reader:
        id_, alert_symbol, alert_price, alert_datatime = row[0], row[1], float(row[4].split()[-1]), \
            convert_date_into_utc(row[5])
        klines_data = get_historical_klines(end_str=alert_datatime, symbol=alert_symbol)

        if klines_data is None:
            # в случае записи BITCOIN PUMP (не стал обрабатывать этот случай так как данные обычно идут одного формата)
            continue

        print(alert_symbol, " -- ", alert_datatime)

        is_alert_valid, max_1_bar_counter, max_2_bar_counter = find_resistance_level(
            klines_data=klines_data, alert_price=alert_price)
        check_result = get_analysis_result(
            alert_price=alert_price, alert_datatime=alert_datatime, is_alert_valid=is_alert_valid,
            alert_symbol=alert_symbol, id_=id_, max_1_bar_counter=max_1_bar_counter, max_2_bar_counter=max_2_bar_counter)

        note_list.append(check_result)
        if len(note_list)/10 == 1:
            write_csv(file_path=RESULT_PATH, data=note_list)
            note_list = list()


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        print(ex)
        sys.exit()

