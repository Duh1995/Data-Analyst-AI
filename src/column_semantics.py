import re

import pandas as pd


UNIQUE_IDENTIFIER_RATIO = 0.98
CODE_LIKE_RATIO = 0.8
CODE_VALUE_SAMPLE_SIZE = 100
LONG_NUMBER_LENGTH = 5

IDENTIFIER_PHRASES = [
    "row id",
    "order id",
    "customer id",
    "product id",
    "invoice id",
    "transaction id",
    "postal code",
    "zip code",
    "order number",
    "invoice number",
    "transaction number"
]

IDENTIFIER_TOKENS = [
    "id",
    "uuid",
    "guid",
    "sku",
    "key"
]

CODE_TOKENS = [
    "code",
    "postal",
    "zip",
    "postcode",
    "zipcode"
]

DATE_TOKENS = [
    "date",
    "data",
    "time",
    "timestamp",
    "datetime"
]


def normalize_column_name(column_name):
    normalized_name = column_name.lower()
    normalized_name = re.sub(r"[_\-/]+", " ", normalized_name)
    normalized_name = re.sub(r"\s+", " ", normalized_name)

    return normalized_name.strip()


def has_identifier_name(column_name):
    normalized_name = normalize_column_name(column_name)
    tokens = normalized_name.split()

    if any(phrase in normalized_name for phrase in IDENTIFIER_PHRASES):
        return True

    if any(token in tokens for token in IDENTIFIER_TOKENS):
        return True

    if any(token in tokens for token in CODE_TOKENS):
        return True

    return False


def has_date_name(column_name):
    normalized_name = normalize_column_name(column_name)
    tokens = normalized_name.split()

    return any(token in tokens for token in DATE_TOKENS)


def has_sequential_integer_values(series):
    non_null_values = series.dropna()

    if non_null_values.empty:
        return False

    if not pd.api.types.is_integer_dtype(non_null_values):
        return False

    sorted_values = sorted(non_null_values.unique())

    if len(sorted_values) != len(non_null_values):
        return False

    first_value = sorted_values[0]
    expected_values = list(range(first_value, first_value + len(sorted_values)))

    return sorted_values == expected_values


def has_code_like_values(series):
    non_null_values = (
        series
        .dropna()
        .astype(str)
        .head(CODE_VALUE_SAMPLE_SIZE)
    )

    if non_null_values.empty:
        return False

    code_like_count = 0

    for value in non_null_values:
        value = value.strip()
        has_digit = bool(re.search(r"\d", value))
        has_letter = bool(re.search(r"[A-Za-z]", value))
        has_separator = bool(re.search(r"[-_/]", value))
        is_long_number = value.isdigit() and len(value) >= LONG_NUMBER_LENGTH

        if has_digit and (has_letter or has_separator or is_long_number):
            code_like_count += 1

    return code_like_count / len(non_null_values) >= CODE_LIKE_RATIO


def is_identifier_column(column_name, series):
    non_null_values = series.dropna()

    if non_null_values.empty:
        return False

    unique_ratio = non_null_values.nunique() / len(non_null_values)

    if has_date_name(column_name):
        return False

    if has_identifier_name(column_name):
        return True

    if has_sequential_integer_values(series):
        return True

    if (
        unique_ratio >= UNIQUE_IDENTIFIER_RATIO
        and has_code_like_values(series)
    ):
        return True

    return False


def get_identifier_columns(df, date_column=None):
    identifier_columns = []

    for column in df.columns:
        if column == date_column:
            continue

        if is_identifier_column(column, df[column]):
            identifier_columns.append(column)

    return identifier_columns


def get_meaningful_numeric_columns(df, identifier_columns):
    meaningful_numeric_columns = []

    for column in df.select_dtypes(include=["int64", "float64"]).columns:
        if column not in identifier_columns:
            meaningful_numeric_columns.append(column)

    return meaningful_numeric_columns


def get_meaningful_categorical_columns(df, identifier_columns, date_column):
    meaningful_categorical_columns = []

    for column in df.select_dtypes(include=["object"]).columns:
        if column in identifier_columns:
            continue

        if column == date_column:
            continue

        if has_date_name(column):
            continue

        if df[column].nunique() <= 1:
            continue

        meaningful_categorical_columns.append(column)

    return meaningful_categorical_columns


def classify_columns(df, date_column=None):
    identifier_columns = get_identifier_columns(
        df,
        date_column=date_column
    )

    return {
        "identifier_columns": identifier_columns,
        "meaningful_numeric_columns": get_meaningful_numeric_columns(
            df,
            identifier_columns
        ),
        "meaningful_categorical_columns": get_meaningful_categorical_columns(
            df,
            identifier_columns,
            date_column
        )
    }
