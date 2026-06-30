import pandas as pd


CSV_ENCODINGS = [
    "utf-8",
    "utf-8-sig",
    "cp1252",
    "latin-1"
]


def load_csv_with_fallback(uploaded_file):
    last_error = None

    for encoding in CSV_ENCODINGS:
        uploaded_file.seek(0)

        try:
            return pd.read_csv(
                uploaded_file,
                encoding=encoding
            )

        except UnicodeDecodeError as error:
            last_error = error

    raise last_error


def load_data(uploaded_file):
    uploaded_file.seek(0)

    if uploaded_file.name.endswith(".csv"):
        return load_csv_with_fallback(uploaded_file)

    return pd.read_excel(uploaded_file)
