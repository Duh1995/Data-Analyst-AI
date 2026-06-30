def answer_question(question, profile, df):

    question = question.lower()

    row_keywords = [
        "row",
        "rows",
        "record",
        "records",
        "entry",
        "entries",
        "observation",
        "observations"
    ]

    column_keywords = [
        "column",
        "columns",
        "field",
        "fields"
    ]

    null_keywords = [
        "null",
        "missing",
        "empty"
    ]

    duplicate_keywords = [
        "duplicate",
        "duplicates",
        "duplicated"
    ]

    numeric_keywords = [
        "numeric",
        "number",
        "numerical"
    ]

    categorical_keywords = [
        "categorical",
        "category",
        "categories"
    ]

    key_keywords = [
        "primary key",
        "unique key",
        "identifier",
        "id"
    ]

    date_keywords = [
        "date",
        "time",
        "datetime"
    ]
    average_keywords = [
    "average",
    "mean"
    ]


    if any(word in question for word in row_keywords):
        return f"The dataset contains {profile['rows']} rows."

    elif any(word in question for word in column_keywords):
        return f"The dataset contains {profile['columns']} columns."

    elif any(word in question for word in null_keywords):
        return f"The dataset contains {profile['total_nulls']} missing values."

    elif any(word in question for word in duplicate_keywords):
        return f"The dataset contains {profile['duplicate_count']} duplicated rows."

    elif any(word in question for word in numeric_keywords):
        return f"The dataset contains {len(profile['numeric_columns'])} numeric columns."

    elif any(word in question for word in categorical_keywords):
        return f"The dataset contains {len(profile['categorical_columns'])} categorical columns."

    elif any(word in question for word in key_keywords):

        if profile["possible_keys"]:
            return (
                "Possible unique keys: "
                + ", ".join(profile["possible_keys"])
            )

        return "No possible unique key was found."

    elif any(word in question for word in date_keywords):

        if profile["date_column"]:
            return f"The detected date column is '{profile['date_column']}'."

        return "No date column was detected."

    

    elif any(word in question for word in average_keywords):

        for column in df.columns:

            if column.lower() in question:

                if column in profile["numeric_columns"]:

                    average = df[column].mean()

                    return (
                        f"The average value of '{column}' "
                        f"is {average:.2f}."
                    )

                return f"'{column}' is not a numeric column, so I can't calculate an average."

        return "I couldn't identify a numeric column in your question."

    return "Sorry, I don't understand that question yet."
