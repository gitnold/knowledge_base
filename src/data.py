import pandas as pd
from pandas import DataFrame


def read_csv_file() -> DataFrame:
    # read csv data into dataframe.
    dataframe: DataFrame = pd.read_csv("../data/macademia_kb_final.csv")
    df_clean = dataframe.drop_duplicates(subset=['name', 'type'])
    
    if df_clean.isnull().values.any() > 0:
        df_clean.fillna("Unspecified", inplace=True)
    # json_dataframe = pd.read_json("../macadamia_kb.json")
    return df_clean
