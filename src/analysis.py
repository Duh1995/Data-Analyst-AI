def get_data_types(df):
    dtypes_df = df.dtypes.reset_index()
    dtypes_df.columns = ["Coluna", "Tipo"]
    return dtypes_df

def get_statistics(df):
    return df.describe()