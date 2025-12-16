
# z3_backend.py
import z3
from z3 import Solver, Bool, Or, Not, sat
from collections import defaultdict
import math

def z3_find_diseases_general(diseases_dict, observed_values, max_models=30):
    """
    diseases_dict: as from kb_loader.load_kb()
    observed_values: list of user-observed strings (already lowercased)
    Returns: list of (disease_name, score, supporting_fields)
    Score = frequency across models (higher better) with tie-break by appearance order.
    """

    # Build disease -> Bool
    disease_names = list(diseases_dict.keys())
    disease_vars = {d: Bool(f"d_{i}") for i, d in enumerate(disease_names)}

    # gather all property values across all properties
    # mapping: prop_val -> Bool
    prop_values = {}
    # for reverse mapping prop_val -> list of (disease, prop_name)
    prop_to_diseases = defaultdict(list)

    def register_prop(dname, prop_name, val):
        if not val:
            return
        if isinstance(val, list):
            for v in val:
                v_clean = v.strip().lower()
                if v_clean == "":
                    continue
                if v_clean not in prop_values:
                    prop_values[v_clean] = Bool(f"p_{len(prop_values)}")
                prop_to_diseases[v_clean].append((dname, prop_name))
        else:
            v_clean = str(val).strip().lower()
            if v_clean == "":
                return
            if v_clean not in prop_values:
                prop_values[v_clean] = Bool(f"p_{len(prop_values)}")
            prop_to_diseases[v_clean].append((dname, prop_name))

    # Register props: name, type, causal_agent, region, control_methods, symptoms, treatments
    for dname, props in diseases_dict.items():
        register_prop(dname, "name", dname)
        register_prop(dname, "type", props.get("type"))
        register_prop(dname, "causal_agent", props.get("causal_agent"))
        register_prop(dname, "region", props.get("region"))
        register_prop(dname, "symptoms", props.get("symptoms") or [])
        register_prop(dname, "treatments", props.get("treatments") or [])
        register_prop(dname, "control_methods", props.get("control_methods") or [])

    solver = Solver()

    # For each disease and each prop it has, add implication:
    # disease -> prop (so if disease true then property true).
    for pval, pairs in prop_to_diseases.items():
        pvar = prop_values[pval]
        for (dname, prop_name) in pairs:
            dvar = disease_vars[dname]
            solver.add(Or(Not(dvar), pvar))

    # Now assert observed values: if unknown prop value create new var and assert it true
    for obs in observed_values:
        key = obs.strip().lower()
        if key == "":
            continue
        if key in prop_values:
            solver.add(prop_values[key])
        else:
            # create fresh prop var (we want it true so only diseases that imply it survive)
            new_var = Bool(f"external_{len(prop_values)}")
            prop_values[key] = new_var
            solver.add(new_var)
            # No disease implies this external var, so Z3 will still find models with disease_vars any booleans;
            # To make unknown property useful, we also mark: prefer to find diseases whose name/type/treatment includes the query using heuristic below
            # (we'll still enumerate models and score)
            pass

    # enumerate models
    models = []
    while len(models) < max_models and solver.check() == sat:
        m = solver.model()
        # capture disease assignments
        assignment = {d: z3.is_true(m.eval(disease_vars[d])) for d in disease_vars}
        models.append(assignment)
        # block this model
        block = Or(*[disease_vars[d] if not val else Not(disease_vars[d]) for d, val in assignment.items()])
        solver.add(block)

    # score diseases by frequency of being True across models
    freq = {d: 0 for d in disease_names}
    for mod in models:
        for d, val in mod.items():
            if val:
                freq[d] += 1

    total_models = max(1, len(models))
    results = []
    for d in disease_names:
        if freq[d] > 0:
            supporting = []
            # find which observed keys are matched by this disease
            for obs in observed_values:
                k = obs.strip().lower()
                if k in prop_to_diseases:
                    pairs = prop_to_diseases[k]
                    # if this disease appears in pairs, note prop_names
                    for (dn, prop_name) in pairs:
                        if dn == d:
                            supporting.append((k, prop_name))
                else:
                    # check substring in name/type/causal_agent etc
                    props = diseases_dict[d]
                    if k in d.lower():
                        supporting.append((k, "name"))
                    elif k and k == props.get("type", ""):
                        supporting.append((k, "type"))
                    elif k and k == props.get("causal_agent", ""):
                        supporting.append((k, "causal_agent"))
                    elif k and k in (props.get("symptoms") or []):
                        supporting.append((k, "symptom"))
                    elif k and k in (props.get("treatments") or []):
                        supporting.append((k, "treatment"))
                    elif k and k in (props.get("control_methods") or []):
                        supporting.append((k, "control_method"))
                    elif k and k == props.get("region", ""):
                        supporting.append((k, "region"))

            score = freq[d] / total_models
            results.append((d, score, supporting))

    # fallback: if no results (no disease var ever true), perform heuristic string-match ranking
    if not results:
        # quick heuristic scoring by matches in fields
        heur = []
        for d, props in diseases_dict.items():
            s = 0.0
            for obs in observed_values:
                q = obs.lower()
                if q in d.lower():
                    s += 2.0
                if q and q == props.get("type"):
                    s += 1.5
                if q and q == props.get("causal_agent"):
                    s += 1.4
                if q and q in (props.get("symptoms") or []):
                    s += 1.0
                if q and q in (props.get("treatments") or []):
                    s += 0.8
                if q and q == props.get("region"):
                    s += 0.5
                if q and q in (props.get("control_methods") or []):
                    s += 0.4
            if s > 0:
                heur.append((d, s, []))
        heur.sort(key=lambda x: x[1], reverse=True)
        return heur

    # sort results by score desc then by name
    results.sort(key=lambda x: (-x[1], x[0]))
    return results
