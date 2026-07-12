def normalize_column_name(column_name):
    return str(column_name).lower().replace("_", " ").replace("-", " ")


def column_matches_keywords(column_name, keywords):
    normalized_name = normalize_column_name(column_name)

    return any(keyword in normalized_name for keyword in keywords)


def find_columns_by_keywords(columns, keywords):
    return [
        column
        for column in columns
        if column_matches_keywords(column, keywords)
    ]


def find_business_numeric_columns(profile, keywords):
    columns = find_columns_by_keywords(
        profile.get("meaningful_numeric_columns", []),
        keywords
    )

    for column in find_columns_by_keywords(profile.get("numeric_columns", []), keywords):
        if column not in columns:
            columns.append(column)

    return columns


def calculate_numeric_column_metrics(df, column):
    if df is None or column not in df.columns:
        return None

    series = df[column].dropna()

    if series.empty:
        return None

    return {
        "total": round(float(series.sum()), 2),
        "average": round(float(series.mean()), 2),
        "min": round(float(series.min()), 2),
        "max": round(float(series.max()), 2),
        "count": int(series.count())
    }


def build_numeric_metric_group(profile, df, keywords):
    columns = find_business_numeric_columns(profile, keywords)
    metrics_by_column = {}

    for column in columns:
        column_metrics = calculate_numeric_column_metrics(df, column)

        if column_metrics is not None:
            metrics_by_column[column] = column_metrics

    return {
        "available": bool(columns),
        "columns": columns,
        "metrics_by_column": metrics_by_column
    }


def build_customer_metrics(profile, df):
    columns = find_columns_by_keywords(
        (
            profile.get("meaningful_categorical_columns", [])
            + profile.get("identifier_columns", [])
        ),
        ["customer", "client", "consumer"]
    )
    unique_counts = {}

    for column in columns:
        if df is not None and column in df.columns:
            unique_counts[column] = int(df[column].nunique())

    return {
        "available": bool(columns),
        "columns": columns,
        "unique_counts": unique_counts
    }


def build_data_quality_metrics(profile):
    return {
        "null_count": int(profile.get("null_count", 0)),
        "null_percentage": float(profile.get("null_percentage", 0)),
        "duplicate_count": int(profile.get("duplicate_count", 0))
    }


def build_business_metrics(profile, df):
    return {
        "sales": build_numeric_metric_group(
            profile,
            df,
            ["sales", "sale", "revenue", "amount"]
        ),
        "profitability": build_numeric_metric_group(
            profile,
            df,
            ["profit", "margin"]
        ),
        "customers": build_customer_metrics(profile, df),
        "data_quality": build_data_quality_metrics(profile)
    }
