import plotly.express as px


def aggregate_metric_by_category(df, category_column, metric_column):
    if (
        df is None
        or category_column not in df.columns
        or metric_column not in df.columns
    ):
        return df

    return (
        df[[category_column, metric_column]]
        .dropna()
        .groupby(category_column, dropna=True)[metric_column]
        .sum()
        .reset_index()
    )


def create_line_chart(df, x_col, y_col):

    fig = px.line(
        df,
        x=x_col,
        y=y_col,
        title=f"{y_col} ao longo de {x_col}"
    )

    return fig

def create_bar_chart(df, x_col, y_col):

    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        title=f"{y_col} por {x_col}"
    )

    return fig


def create_scatter_chart(df, x_col, y_col):

    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        title=f"{y_col} por {x_col}"
    )

    return fig


def create_histogram(df, column):

    fig = px.histogram(
        df,
        x=column,
        title=f"Distribuição de {column}"
    )

    return fig
