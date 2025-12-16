import csv
import ast
from z3 import *

# Z3 ENGINE SETUP
fp = Fixedpoint()
fp.set(engine='datalog')  # Use Datalog engine for database-like reasoning
Thing = BitVecSort(32)    # Define a custom type (mapped to 32-bit integers)

# STRING-TO-ID MAPPING
# Z3 requires numeric values, so we map strings to unique BitVector IDs.
str_to_id = {}
id_to_str = {}
id_counter = 1

def get_id(text):
    """Converts a string to a unique Z3 BitVector ID."""
    global id_counter
    if not text: return None

    clean_text = text.strip().strip("'").strip('"')
    if clean_text not in str_to_id:
        val = BitVecVal(id_counter, Thing)
        str_to_id[clean_text] = val
        id_to_str[id_counter] = clean_text
        id_counter += 1
    return str_to_id[clean_text]

def get_name(z3_val):
    """Converts a Z3 ID back to its original string representation."""
    try:
        return id_to_str.get(z3_val.as_long(), str(z3_val))
    except:
        return str(z3_val)

# RELATION DEFINITIONS
# Define the predicates (schema) for the Knowledge Base.
is_type = Function('is_type', Thing, Thing, BoolSort())
caused_by = Function('caused_by', Thing, Thing, BoolSort())
has_symptom = Function('has_symptom', Thing, Thing, BoolSort())
treated_with = Function('treated_with', Thing, Thing, BoolSort())

fp.register_relation(is_type)
fp.register_relation(caused_by)
fp.register_relation(has_symptom)
fp.register_relation(treated_with)

# DATA LOADING
z3_facts_output = []

def add_fact(relation, arg1, arg2):
    """Asserts a fact in Z3 and logs it for file export."""
    fp.fact(relation(arg1, arg2))
    # Store in SMT-LIB format for external validation
    z3_facts_output.append(f"(rule ({relation.name()} {arg1.as_long()} {arg2.as_long()}))")

print("Loading data from CSV...")
csv_filename = '../data/macademia_kb_final.csv'

try:
    with open(csv_filename, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            subject = get_id(row['name'])

            if row.get('type'):
                add_fact(is_type, subject, get_id(row['type']))

            if row.get('causal_agent'):
                add_fact(caused_by, subject, get_id(row['causal_agent']))

            # Parse symptoms list string -> individual facts
            if row.get('symptoms'):
                try:
                    for sym in ast.literal_eval(row['symptoms']):
                        add_fact(has_symptom, subject, get_id(sym))
                except: pass

            # Parse treatments list string -> individual facts
            if row.get('treatments'):
                try:
                    for treat in ast.literal_eval(row['treatments']):
                        # Logic: Treatment (Arg1) treats Subject (Arg2)
                        add_fact(treated_with, get_id(treat), subject)
                except: pass
except FileNotFoundError:
    print(f"Error: '{csv_filename}' not found.")
    exit()

# EXPORT FACTS TO FILE
# Generates a .z3 file containing the raw logic facts.
with open('macadamia.z3', 'w') as f:
    f.write("; Macadamia Knowledge Base - Z3 Facts\n")
    f.write("; --- ID MAPPING ---\n")
    for name, z3_val in str_to_id.items():
        f.write(f"; {z3_val.as_long()} = {name}\n")

    f.write("\n; --- FACTS ---\n")
    for line in z3_facts_output:
        f.write(line + "\n")

print("Knowledge Base loaded and exported.")

# LOGIC RULES IMPLEMENTATION

# Define variables for the rule
t, d, s = Consts('t d s', Thing)
fp.declare_var(t, d, s) # Declare as universal variables for the engine

# Define and register the new inferred relation
cures_symptom = Function('cures_symptom', Thing, Thing, BoolSort())
fp.register_relation(cures_symptom)

# Add the Horn clause (Rule) to the engine
fp.rule(cures_symptom(t, s), [treated_with(t, d), has_symptom(d, s)])
print("Logic rules registered.")

# SOLVER EXECUTION
print("\n--- Running Prover ---")
test_symptom = "Holes in nuts"
target_id = get_id(test_symptom)

print(f"Query: What cures '{test_symptom}'?")

# Define query variable
q = Const('q', Thing)
fp.declare_var(q)

# Query the engine
result = fp.query(cures_symptom(q, target_id))

if result == sat:
    print("Solution Found (SAT)")
    ans = fp.get_answer()
    arg = ans.arg(0)

    # Handle multiple results vs single result
    if arg.num_args() > 0:
         for i in range(arg.num_args()):
             print(f"  -> Recommended: {get_name(arg.arg(i))}")
    else:
        print(f"  -> Recommended: {get_name(arg)}")
else:
    print("No solution found (UNSAT)")
