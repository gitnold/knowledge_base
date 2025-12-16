
# kb_loader.py
import csv
import ast
import re

def parse_prolog_kb(prolog_text):
    """
    Copied/adapted from your uploaded parser (robust to several prolog fact styles).
    Returns disease -> dict with keys: type, causal_agent, symptoms(list), treatments(list), region, control_methods(list)
    """
    disease_to_symptoms = {}

    # disease(NAME, [sym1, sym2]).
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
        disease_to_symptoms.setdefault(name, []).extend(syms)

    # disease(NAME).
    pat_name_only = re.compile(r"disease\(\s*'?(?P<name>[^']+)'?\s*\)\s*\.", re.IGNORECASE)
    for m in pat_name_only.finditer(prolog_text):
        name = m.group('name').strip()
        disease_to_symptoms.setdefault(name, [])

    # symptom_of('symptom','Disease') and symptom('Disease','symptom')
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

    # Also try to parse other fields if present in a simple style:
    # e.g. type('Name','fungal'). causal_agent('Name','X'). treatment('Name',['a','b']).
    def simple_list_field(field_name):
        pat = re.compile(rf"{field_name}\(\s*'?(?P<name>[^']+)'?\s*,\s*\[(?P<items>[^\]]*)\]\s*\)\s*\.", re.IGNORECASE)
        for m in pat.finditer(prolog_text):
            name = m.group('name').strip()
            items_raw = m.group('items').strip()
            items = []
            if items_raw:
                for s in re.split(r',\s*', items_raw):
                    items.append(re.sub(r"^\\s*'?|'?\\s*$", '', s.strip()).lower())
            disease_to_symptoms.setdefault(name, []).extend(items)

    # There's no guarantee these extra keys exist; this function is provided for extensibility.

    # Build final dict with empty fields and normalized symptoms list
    facts = {}
    for d, syms in disease_to_symptoms.items():
        clean = [s.strip().lower() for s in syms if s]
        facts[d] = {
            "type": "",
            "causal_agent": "",
            "symptoms": list(dict.fromkeys(clean)),
            "treatments": [],
            "region": "",
            "control_methods": []
        }
    return facts


def load_kb_from_csv(csv_path):
    """Load CSV with expected columns: name,type,causal_agent,symptoms,treatments,region,control_methods"""
    data = {}
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['name'].strip()
            # helper to parse lists stored as Python list strings in CSV
            def _parse_list_field(v):
                if not v:
                    return []
                try:
                    parsed = ast.literal_eval(v)
                    if isinstance(parsed, (list, tuple)):
                        return [str(x).strip().lower() for x in parsed]
                    # fallback: comma split
                    return [x.strip().lower() for x in str(v).split(",") if x.strip()]
                except:
                    return [x.strip().lower() for x in str(v).split(",") if x.strip()]

            data[name] = {
                "type": (row.get("type") or "").strip().lower(),
                "causal_agent": (row.get("causal_agent") or "").strip().lower(),
                "symptoms": _parse_list_field(row.get("symptoms")),
                "treatments": _parse_list_field(row.get("treatments")),
                "region": (row.get("region") or "").strip().lower(),
                "control_methods": _parse_list_field(row.get("control_methods"))
            }
    return data


def load_kb(csv_path=None, prolog_path=None):
    """
    Prefer CSV if provided; otherwise try Prolog.
    Returns diseases dict as:
      { "Disease Name": { type, causal_agent, symptoms:list, treatments:list, region, control_methods:list } }
    """
    if csv_path:
        return load_kb_from_csv(csv_path)
    if prolog_path:
        with open(prolog_path, "r", encoding="utf-8") as f:
            content = f.read()
        return parse_prolog_kb(content)
    return {}
