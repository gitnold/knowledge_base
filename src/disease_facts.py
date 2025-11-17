from pandas.core.frame import DataFrame
import plgnrtor
import data

def run():
    dataframe = data.read_csv_file()
    plgnrtor.write_facts_to_file(write_causal_agent(dataframe))

def write_causal_agent(df: DataFrame) -> list[str]:
    # approach one.
    # grouped = df.groupby('type').agg({
    #     'name' : list,
    #     'causal_agent' : list
    # }).reset_index()

    # approach two.
    names = df[df['type'] == 'Disease']['name'].to_list()
    causes = df[df['type'] == 'Disease']['causal_agent'].to_list()

    count = 0
    prolog_facts: list[str] = list()
    prolog_facts.append("\n\n% Causal agents of various diseases\n")
    for name in names:
        prolog_facts.append(f"caused_by('{name}', '{causes[count]}').\n")
        count += 1

    return prolog_facts


if __name__ == "__main__":
    run()
