
# streamlit_app.py
import streamlit as st
from kb_loader import load_kb
from z3_backend import z3_find_diseases_general
from search_engine import tokenize_query
import json
import os

st.set_page_config(page_title="Z3 Disease Search", layout="wide")
st.title("Z3 Disease Search (Z3-only)")

st.markdown("""
Enter free text describing **any** of: `name`, `type`, `causal_agent`, `symptoms`, `treatments`, `region`, `control_methods`.
The app will prioritize identifying the disease that best explains the observation(s) using Z3 constraints.
""")

# Sidebar: KB selection
st.sidebar.header("Knowledge Base")
kb_choice = st.sidebar.radio("Load KB from:", ("CSV file", "Prolog file", "Use example bundled (small)") )

uploaded_file = None
if kb_choice == "CSV file":
    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
elif kb_choice == "Prolog file":
    uploaded_file = st.sidebar.file_uploader("Upload Prolog (.pro/.pl/.txt)", type=["pro", "pl", "txt"])

# if example selected, create a small builtin KB
example_kb = {
    "Macadamia Dieback": {
        "type": "fungal",
        "causal_agent": "phytophthora cinnamomi",
        "symptoms": ["wilting", "root rot", "dieback", "yellowing leaves"],
        "treatments": ["phosphite", "fungicide"],
        "region": "east africa",
        "control_methods": ["soil drainage", "resistant rootstocks"]
    },
    "Nut Borer": {
        "type": "insect",
        "causal_agent": "iraeus borer",
        "symptoms": ["holes in nuts", "reduced yield", "chewed kernels"],
        "treatments": ["insecticide", "trapping"],
        "region": "east africa",
        "control_methods": ["bagging nuts", "sanitation"]
    },
    "Leaf Rust": {
        "type": "fungal",
        "causal_agent": "puccinia spp",
        "symptoms": ["orange pustules", "defoliation", "yellowing leaves"],
        "treatments": ["fungicide", "resistant cultivars"],
        "region": "east africa",
        "control_methods": ["resistant cultivars", "timely fungicide"]
    }
}

if kb_choice == "Use example bundled (small)":
    kb = example_kb
else:
    if uploaded_file is None:
        st.sidebar.info("Upload a KB file (CSV/Prolog) or choose the example KB.")
        st.stop()
    else:
        # Save uploaded file to a temp location and load
        save_path = os.path.join(".", "tmp_uploaded_kb")
        os.makedirs(save_path, exist_ok=True)
        file_path = os.path.join(save_path, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        if kb_choice == "CSV file":
            kb = load_kb(csv_path=file_path)
        else:
            kb = load_kb(prolog_path=file_path)

# Main UI: search bar and optional multi-field helpers
query = st.text_input("Search (any parameter)", placeholder="e.g. 'wilting', 'phytophthora', 'phosphite', 'holes in nuts'")

with st.expander("Advanced: provide fields directly"):
    name_field = st.text_input("Name")
    type_field = st.text_input("Type")
    causal_field = st.text_input("Causal agent")
    region_field = st.text_input("Region")
    symptoms_field = st.text_input("Symptoms (comma-separated)")
    treatments_field = st.text_input("Treatments (comma-separated)")
    control_field = st.text_input("Control methods (comma-separated)")

# Collect observed tokens
observed = []
if query:
    observed += tokenize_query(query)

# advanced fields override / supplement
def add_if(v):
    if v and v.strip():
        return tokenize_query(v)
    return []

observed += add_if(name_field)
observed += add_if(type_field)
observed += add_if(causal_field)
observed += add_if(region_field)
observed += add_if(symptoms_field)
observed += add_if(treatments_field)
observed += add_if(control_field)

# dedupe but keep order
seen = set()
observed = [x for x in observed if not (x in seen or seen.add(x))]

st.write(f"Observations: {observed if observed else '— none —'}")

if observed:
    with st.spinner("Querying Z3..."):
        results = z3_find_diseases_general(kb, observed, max_models=30)

    if not results:
        st.error("No diseases matched the observation(s). Try different keywords or add more symptoms.")
    else:
        st.success("Top match:")
        top = results[0]
        top_name, top_score, top_support = top[0], top[1], top[2]
        st.markdown(f"### **{top_name}**  — confidence {top_score:.2f}")

        with st.expander("Details for top match"):
            st.json(kb.get(top_name, {}))

        if len(results) > 1:
            st.subheader("Other candidate diseases (ranked)")
            for d, score, support in results[1:8]:
                st.write(f"**{d}** — score {score:.2f} — matches: {', '.join([f'{k} ({p})' for k,p in support]) if support else '—'}")

        # Show raw results table
        if st.checkbox("Show raw result list"):
            st.write(results)
else:
    st.info("Type a search term to find likely disease(s).")
