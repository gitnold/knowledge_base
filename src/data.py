import pandas as pd
from pandas import DataFrame


def read_csv_file() -> DataFrame:
    # read csv data into dataframe.
    dataframe: DataFrame = pd.read_csv("../data/macadamia_kb_clean.csv")
    # json_dataframe = pd.read_json("../macadamia_kb.json")
    return dataframe
