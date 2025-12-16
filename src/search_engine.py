
# search_engine.py
def tokenize_query(raw_query):
    """
    Turn free text into list of observation tokens.
    Accepts things like:
     - "wilting, yellowing"
     - "phytophthora"
     - "phosphite"
    """
    if not raw_query:
        return []
    # if the user included commas or semicolons, split into items
    if "," in raw_query or ";" in raw_query:
        parts = [p.strip().lower() for p in re.split(r"[;,]", raw_query) if p.strip()]
        return parts
    # otherwise return single string (lowercased)
    return [raw_query.strip().lower()]

import re
