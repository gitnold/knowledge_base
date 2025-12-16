"""
z3_prolog_integration.py  (improved parser)

This script contains:
 - robust Prolog fact parsing (several common patterns)
 - Z3 encoding to find disease assignments consistent with observed symptoms
 - pyswip example usage to call the likely_disease/3 rule in Prolog (if available)

Supported Prolog fact styles (all optional):
    disease('Name').
    disease('Name', ['sym1','sym2']).
    symptom_of('symptom', 'Disease').
    symptom('Disease', 'symptom').

The parser normalizes symptom text to lowercase and strips spaces/quotes.
"""

import re
from z3 import Solver, Bool, Or, Not, sat

# ---- Parsing Prolog facts with support for multiple common styles ----
def parse_prolog_kb(prolog_text):
    disease_to_symptoms = {}

    # 1) disease(NAME, [sym1, sym2]).
    pat_list = re.compile(r"disease\(\s*'?(?P<name>[^']+)'?\s*,\s*\[(?P<syms>[^\]]*)\]\s*\)\s*\.", re.IGNORECASE)
    for m in pat_list.finditer(prolog_text):
        name = m.group('name').strip()
        syms_raw = m.group('syms').strip()
        syms = []
        if syms_raw:
            for s in re.split(r',\s*', syms_raw):
                s_clean = re.sub(r"^\\s*'?|'?\\s*$", '', s.strip().lower())
                if s_clean:
                    syms.append(s_clean)
                    disease_to_symptoms[name] = list(dict.fromkeys(syms))  # keep order, dedupe

    # 2) disease(NAME).  (no symptoms listed)
    pat_name_only = re.compile(r"disease\(\s*'?(?P<name>[^']+)'?\s*\)\s*\.", re.IGNORECASE)
    for m in pat_name_only.finditer(prolog_text):
        name = m.group('name').strip()
        disease_to_symptoms.setdefault(name, [])

    # 3) symptom_of('symptom', 'Disease') or symptom('Disease','symptom')
    pat_sym_of = re.compile(r"symptom_of\(\s*'?(?P<sym>[^']+)'?\s*,\s*'?(?P<d>[^']+)'?\s*\)\s*\.", re.IGNORECASE)
    for m in pat_sym_of.finditer(prolog_text):
        sym = m.group('sym').strip().lower()
        d = m.group('d').strip()
        disease_to_symptoms.setdefault(d, []).append(sym)

    pat_sym = re.compile(r"symptom\(\s*'?(?P<d>[^']+)'?\s*,\s*'?(?P<sym>[^']+)'?\s*\)\s*\.", re.IGNORECASE)
    for m in pat_sym.finditer(prolog_text):
        d = m.group('d').strip()
        sym = m.group('sym').strip().lower()
        disease_to_symptoms.setdefault(d, []).append(sym)

    # Normalize and deduplicate symptom lists
    for d, syms in disease_to_symptoms.items():
        clean = [s.strip().lower() for s in syms if s]
        disease_to_symptoms[d] = list(dict.fromkeys(clean))

    return disease_to_symptoms

# ---- Z3 encoding (same concept, now robust to KB shape) ----
def z3_find_diseases(disease_to_symptoms, observed_symptoms, max_models=10):
    # Map disease -> Bool, symptom -> Bool
    disease_vars = {d: Bool(f"d_{i}") for i, d in enumerate(disease_to_symptoms.keys())}
    # create symptom vars deterministically by symptom string
    all_symptoms = sorted({s for syms in disease_to_symptoms.values() for s in syms})
    symptom_vars = {s: Bool(f"s_{i}") for i, s in enumerate(all_symptoms)}

    solver = Solver()

    # disease -> each symptom it causes
    for d, syms in disease_to_symptoms.items():
        dvar = disease_vars[d]
        for s in syms:
            svar = symptom_vars[s]
            solver.add(Or(Not(dvar), svar))

    # observed symptoms -> assert true (create fresh var if unknown symptom)
    for obs in observed_symptoms:
        key = obs.strip().lower()
        if key in symptom_vars:
            solver.add(symptom_vars[key])
        else:
            # if the observed symptom isn't represented in KB, create a fresh var and assert it
            v = Bool(f"obs_{len(symptom_vars)}")
            symptom_vars[key] = v
            solver.add(v)

    # enumerate models
    models = []
    while len(models) < max_models and solver.check() == sat:
        m = solver.model()
        assignment = {d: bool(m.eval(disease_vars[d])) for d in disease_vars}
        models.append(assignment)
        # block model
        block = Or(*[disease_vars[d] if not val else Not(disease_vars[d]) for d, val in assignment.items()])
        solver.add(block)

    return models

# ---- Example usage when run as a script ----
if __name__ == '__main__':
    kb_path = '../prolog/kb_lists.pro'
    try:
        with open(kb_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print('../prolog/kb_lists.pro not found - please place it next to this script.')
        content = ''

    facts = parse_prolog_kb(content)
    print('Diseases parsed and symptoms (may be empty lists if KB names only):')
    for d, syms in facts.items():
        print(f' - {d}: {syms}')

    observed = ['yellowing leaves', 'wilting']
    print('\\nObserved:', observed)
    models = z3_find_diseases(facts, observed, max_models=6)
    for i, m in enumerate(models):
        positives = [d for d, v in m.items() if v]
        print(f'Model {i+1}: {positives}')
