import csv
import os


def read_csv(file_path: str):

    with open(file_path, encoding='utf-8') as file:
        reader_object = csv.reader(file, delimiter=",")
        for row in reader_object:
            yield row


def create_csv_result_file(file_path: str):

    headers = ('id', "is_valid", "strength", "length", "bar_1", "bar_2", "symbol", "profit (%)")

    if not os.path.exists(path=file_path):
        with open(file_path, "w", encoding='utf-8', newline='') as file:
            writer_object = csv.writer(file, delimiter=",")
            writer_object.writerow(headers)


def write_csv(file_path: str, data: list[list]) -> None:

    with open(file_path, "a", encoding='utf-8', newline='') as file:
        writer_object = csv.writer(file, delimiter=",")
        writer_object.writerows(data)

