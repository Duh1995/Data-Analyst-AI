import csv

import pandas as pd
from pandas.errors import EmptyDataError, ParserError


CSV_ENCODINGS = [
    "utf-8",
    "utf-8-sig",
    "cp1252",
    "latin-1"
]

CSV_DELIMITERS = [
    None,
    ";",
    ",",
    "\t",
    "|"
]


class DataLoadingError(Exception):
    pass


def read_csv_with_options(uploaded_file, encoding, delimiter):
    uploaded_file.seek(0)

    if delimiter is None:
        return pd.read_csv(
            uploaded_file,
            encoding=encoding,
            sep=None,
            engine="python"
        )

    return pd.read_csv(
        uploaded_file,
        encoding=encoding,
        sep=delimiter
    )


def load_csv_with_fallback(uploaded_file):
    last_error = None

    for encoding in CSV_ENCODINGS:
        for delimiter in CSV_DELIMITERS:

            try:
                return read_csv_with_options(
                    uploaded_file,
                    encoding,
                    delimiter
                )

            except (
                UnicodeDecodeError,
                EmptyDataError,
                ParserError,
                csv.Error
            ) as error:
                last_error = error

    raise DataLoadingError(
        "Could not load this CSV file. Please check the file encoding, delimiter, or format."
    ) from last_error


def load_data(uploaded_file):
    uploaded_file.seek(0)

    if uploaded_file.name.lower().endswith(".csv"):
        return load_csv_with_fallback(uploaded_file)

    return pd.read_excel(uploaded_file)
