import profile

import pandas as pd
from src.analysis_catalog import get_analysis_catalog
from src.analysis_resolver import build_analysis_resolution
from src.business_metrics import build_business_metrics
from src.column_semantics import classify_columns
from src.decision_engine import (
    build_business_diagnosis,
    build_business_health,
    build_executive_priorities
)

def get_numeric_columns(df):

    return df.select_dtypes(
        include=["int64", "float64"]
    ).columns.tolist()


def get_date_column(df):

    possible_date_columns = [
        "date",
        "data",
        "order_date",
        "transaction_date",
        "timestamp"
    ]

    for col in df.columns:

        if col.lower() in possible_date_columns:
            return col

    for col in df.columns:

        if df[col].dtype == "object":

            try:

                pd.to_datetime(df[col])

                return col

            except:
                pass

    return None

def get_categorical_columns(df):

    return df.select_dtypes(
        include=["object"]
    ).columns.tolist()

def get_duplicate_count(df):

    return df.duplicated().sum()

def get_null_count(df):

    return df.isnull().sum().sum()

def get_null_percentage(df):

    total_cells = df.shape[0] * df.shape[1]

    if total_cells == 0:
        return 0

    null_count = get_null_count(df)

    return round((null_count / total_cells) * 100, 2)

def get_memory_usage(df):

    memory = df.memory_usage(deep=True).sum()

    return round(memory / 1024 / 1024, 2)

def get_possible_keys(df):

    possible_keys = []

    for col in df.columns:

        if df[col].nunique() == len(df):

            possible_keys.append(col)

    return possible_keys

def get_cardinality(df):

    cardinality = {}

    for col in df.columns:

        cardinality[col] = df[col].nunique()

    return cardinality

def get_top_categories(df):

    top_categories = {}

    for col in get_categorical_columns(df):

        top_categories[col] = (
            df[col]
            .value_counts(normalize=True)
            .head(5)
            .round(3)
            .to_dict()
        )

    return top_categories

def get_chart_recommendation(profile):

    if (
        profile["date_column"] is not None
        and len(profile["meaningful_numeric_columns"]) > 0
    ):
        return "line"

    if (
        len(profile["meaningful_categorical_columns"]) > 0
        and len(profile["meaningful_numeric_columns"]) > 0
    ):
        return "bar"

    if len(profile["meaningful_numeric_columns"]) > 0:
        return "histogram"

    return None

def generate_insights(profile):

    insights = []

    insights.append(
        f"O dataset contém {profile['rows']} registos distriuidos por {profile['columns']} colunas."
    )


    if profile["null_count"] == 0:

        insights.append(
            "Não foram encontrados valores nulos."
        )

    else:

        insights.append(
            f"Foram encontrados {profile['null_count']} valores nulos."
        )

    if profile["possible_keys"]:

        insights.append(
            f"Foi identificada uma possível chave única: {profile['possible_keys'][0]}"
        )

    insights.append(
    f"O dataset contém {len(profile['numeric_columns'])} variáveis numéricas e {len(profile['categorical_columns'])} categóricas."
    )

    return insights

def build_profile(df):
    date_column = get_date_column(df)
    column_semantics = classify_columns(
        df,
        date_column=date_column
    )
    identifier_columns = column_semantics.get(
        "identifier_columns",
        []
    )
    meaningful_numeric_columns = column_semantics.get(
        "meaningful_numeric_columns",
        []
    )
    meaningful_categorical_columns = column_semantics.get(
        "meaningful_categorical_columns",
        []
    )
    
    profile = {
        "rows": df.shape[0],
        "columns": df.shape[1],
        "date_column": date_column,
        "numeric_columns": get_numeric_columns(df),
        "categorical_columns": get_categorical_columns(df),
        "identifier_columns": identifier_columns,
        "meaningful_numeric_columns": meaningful_numeric_columns,
        "meaningful_categorical_columns": meaningful_categorical_columns,
        "null_count": get_null_count(df),
        "null_percentage": get_null_percentage(df),
        "duplicate_count": get_duplicate_count(df),
        "profile_memory": get_memory_usage(df),
        "possible_keys": get_possible_keys(df),
        "cardinality": get_cardinality(df),
        "top_categories": get_top_categories(df),
        "total_nulls": df.isnull().sum().sum()
    }
    profile["business_diagnosis"] = build_business_diagnosis(profile)
    profile["business_metrics"] = build_business_metrics(profile, df)
    profile["business_health"] = build_business_health(profile)
    profile["available_analyses"] = build_analysis_resolution(
        profile,
        get_analysis_catalog()
    )
    profile["executive_priorities"] = build_executive_priorities(
        profile["available_analyses"],
        profile["business_health"],
        profile["business_diagnosis"]
    )
    profile["recommended_chart"] = get_chart_recommendation(profile)
    profile["insights"] = generate_insights(profile)

    return profile

