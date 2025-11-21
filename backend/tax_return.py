from typing import Dict, Any, List, Optional

def init_tax_return() -> Dict[str, Any]:
    """
    Initialize a new tax_return object. Keep keys stable and documented.
    """
    return {
        "taxpayer": {
            "first_name": None,
            "last_name": None,
            "ssn": None,
            "filing_status": None,
            "address": None,
        },
        "w2s": [],        # list[dict]
        "1099ints": [],   # list[dict]
        "1099necs": [],   # list[dict]
        "totals": {
            "wages": 0.0,
            "interest_income": 0.0,
            "self_employment_income": 0.0,
            "federal_tax_withheld": 0.0,
            "state_tax_withheld": 0.0,
            # optionally derived fields:
            "agi": 0.0,
            "taxable_income": 0.0,
        }
    }

# Adders (idempotent / safe to call multiple times)
def add_1099_int_to_tax_return(tax_return: Dict[str, Any], form: Dict[str, Any]) -> None:
    tax_return["1099ints"].append(form)
    tax_return["totals"]["interest_income"] += float(form.get("interest_income", 0.0) or 0.0)
    tax_return["totals"]["federal_tax_withheld"]  += float(form.get("federal_tax_withheld", 0.0) or 0.0)
    tax_return["totals"]["state_tax_withheld"]    += float(form.get("state_tax_withheld", 0.0) or 0.0)

def add_w2_to_tax_return(tax_return: Dict[str, Any], form: Dict[str, Any]) -> None:
    tax_return["w2s"].append(form)
    tax_return["totals"]["wages"] += float(form.get("wages", 0.0) or 0.0)
    tax_return["totals"]["federal_tax_withheld"] += float(form.get("federal_tax_withheld", 0.0) or 0.0)
    tax_return["totals"]["state_tax_withheld"] += float(form.get("state_tax_withheld", 0.0) or 0.0)

def add_1099_nec_to_tax_return(tax_return: Dict[str, Any], form: Dict[str, Any]) -> None:
    tax_return["1099necs"].append(form)
    nec_income = float(form.get("nonemployee_compensation", 0.0) or 0.0)
    tax_return["totals"]["self_employment_income"] += nec_income
    tax_return["totals"]["federal_tax_withheld"] += float(form.get("federal_tax_withheld", 0.0) or 0.0)
    tax_return["totals"]["state_tax_withheld"] += float(form.get("state_tax_withheld", 0.0) or 0.0)

# Small utility to recompute totals from raw lists (useful if you need to recalc)
def recompute_totals(tax_return: Dict[str, Any]) -> None:
    totals = {
        "wages": 0.0,
        "interest_income": 0.0,
        "self_employment_income": 0.0,
        "federal_tax_withheld": 0.0,
        "state_tax_withheld": 0.0,
        "agi": 0.0,
        "taxable_income": 0.0,
    }

    for w in tax_return.get("w2s", []):
        totals["wages"] += float(w.get("wages", 0.0) or 0.0)
        totals["federal_tax_withheld"] += float(w.get("federal_tax_withheld", 0.0) or 0.0)
        totals["state_tax_withheld"] += float(w.get("state_tax_withheld", 0.0) or 0.0)

    for i in tax_return.get("1099ints", []):
        totals["interest_income"] += float(i.get("interest_income", 0.0) or 0.0)
        totals["federal_tax_withheld"] += float(i.get("federal_tax_withheld", 0.0) or 0.0)
        totals["state_tax_withheld"] += float(i.get("state_tax_withheld", 0.0) or 0.0)

    for n in tax_return.get("1099necs", []):
        totals["self_employment_income"] += float(n.get("nonemployee_compensation", 0.0) or 0.0)
        totals["federal_tax_withheld"] += float(n.get("federal_tax_withheld", 0.0) or 0.0)
        totals["state_tax_withheld"] += float(n.get("state_tax_withheld", 0.0) or 0.0)

    # write back computed totals
    tax_return["totals"].update(totals)
