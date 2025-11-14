import data
import pandas as pd
from enum import Enum, auto
import ast

class ColumnType(Enum):
    SYMPTOM = auto(),
    TREATMENT = auto(),
    CONTROL = auto(),


def run():
    dataframe = data.read_csv_file()
    groups = dict(tuple(dataframe.groupby("type")))
    # inplace comparisons is also a technique instead of separate dataframes.

    df_a = groups["pest"]
    df_b = groups["disease"]

    #running the code generator.
    write_facts_to_file(generate_disease_facts(df_b))
    write_facts_to_file(generate_pest_facts(df_a))
    write_facts_to_file(generate_list_facts(dataframe, ColumnType.SYMPTOM))
    write_facts_to_file(generate_list_facts(dataframe, ColumnType.CONTROL))
    write_facts_to_file(generate_list_facts(dataframe, ColumnType.TREATMENT))


#FIX: make sure facts are grouped together.
def generate_disease_facts(dataframe: pd.DataFrame) -> list[str]:
    diseases = dataframe["name"].to_list()
    prolog_facts: list[str] = list()
    for disease in diseases:
        prolog_facts.append(f"disease('{disease}').\n")
    regions = dataframe['region'].to_list()
    count = 0
    for region in regions:
        prolog_facts.append(f"found('{diseases[count]}', {region.split(',')}).\n")
        count += 1

    return prolog_facts


def generate_pest_facts(dataframe: pd.DataFrame) -> list[str]:
    pests = dataframe["name"].to_list()
    prolog_facts: list[str] = list()
    for pest in pests:
        prolog_facts.append(f"pest('{pest}').\n")
    regions = dataframe['region'].to_list()
    count = 0
    for region in regions:
        prolog_facts.append(f"found('{pests[count]}', {region.split(',')}).\n")
        count += 1
    return prolog_facts

def handle_list_fields(values: list) -> list[str]:
    pass
    return ['a']

def write_facts_to_file(facts: list[str]) -> int:
    filepath = "knowledgebase.pro"
    status = 0
    # try block below might be redundant as write operations create new file if missing.
    # check if a file exists first to determine mode to open fiule in.
    try:
        with open(filepath, "a") as pl_file:
            for fact in facts:
                status = pl_file.write(fact)
    except FileNotFoundError:
        raise BaseException(f"File {filepath} not found!")

    return status



def generate_rules():
    pass

#TODO: make function below generic of sorts.
def generate_list_facts(dataframe: pd.DataFrame, relation: ColumnType) -> list[str]:
    prolog_facts = list()
    names = dataframe['name'].to_list()
    count = 0
    current_value = ""

    # Choose the correct column and relation name
    match relation:
        case ColumnType.SYMPTOM:
            values = dataframe['symptoms'].to_list()
            current_value = "symptoms"

        case ColumnType.TREATMENT:
            values = dataframe['treatments'].to_list()
            current_value = "treatments"

        case ColumnType.CONTROL:
            values = dataframe['control_methods'].to_list()
            current_value = "controlMethods"

    # Process each entry
    for value in values:
        # Safely convert stringified list → Python list
        try:
            parsed_list = ast.literal_eval(value) if isinstance(value, str) else value
        except Exception:
            parsed_list = [value]

        # Wrap each entry as a single-quoted atom for Prolog
        cleaned = [f"'{s.strip()}'" for s in parsed_list]

        prolog_facts.append(
            f"{current_value}('{names[count]}', [{', '.join(cleaned)}]).\n"
        )
        count += 1

    return prolog_facts




