
from pandas.core.frame import DataFrame

import data
import plgnrtor


def run():
    dataframe = data.read_csv_file()
    plgnrtor.write_facts_to_file(write_scientific_name(dataframe))

def write_scientific_name(df: DataFrame) -> list[str]:
    # approach one.
    # grouped = df.groupby('type').agg({
    #     'name' : list,
    #     'causal_agent' : list
    # }).reset_index()

    # approach two.
    pests = df[df['type'] == 'Pest']['name'].to_list()
    names = df[df['type'] == 'Pest']['causal_agent'].to_list()

    count = 0
    prolog_facts: list[str] = list()
    prolog_facts.append("\n\n% scientific names of various pests\n")
    for pest in pests:
        prolog_facts.append(f"scientific_name('{pest}', '{names[count]}').\n")
        count += 1

    return prolog_facts


if __name__ == "__main__":
    run()
