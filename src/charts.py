import pandas as pd
import plotly.express as px

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

def create_histogram(df, column):

    fig = px.histogram(
        df,
        x=column,
        title=f"Distribuição de {column}"
    )

    return fig