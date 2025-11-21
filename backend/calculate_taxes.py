import json
import datetime

# Load tax configuration
try:
    with open("./backend/tax_config.json", 'r') as file:
        tax_data = json.load(file)
except FileNotFoundError:
    print("Error: tax_config.json not found in the expected location.")
    tax_data = {}  # Initialize empty to prevent crashes


def calculate_gross_income(w2s, ints, necs):
    """Sum all income sources."""
    wages = sum(w2.get("wages", 0.0) for w2 in w2s)
    interest_income = sum(i.get("interest_income", 0.0) for i in ints)
    self_employment_income = sum(n.get("nonemployee_compensation", 0.0) for n in necs)
    gross_income = wages + interest_income + self_employment_income
    return wages, interest_income, self_employment_income, gross_income


def calculate_taxable_income(gross_income, filing_status, year):
    """Subtract standard deduction to get taxable income."""
    standard_deduction = tax_data[year]["standard_deductions"].get(filing_status, 0.0)
    taxable_income = max(0, gross_income - standard_deduction)
    return taxable_income, standard_deduction


def calculate_tax_owed(taxable_income, filing_status, year):
    """Calculate federal tax owed using tax brackets."""
    brackets = tax_data[year]["tax_brackets"].get(filing_status, [])
    tax_owed = 0.0
    for bracket in brackets:
        bracket_min = bracket["min"]
        bracket_max = bracket["max"]
        rate = bracket["rate"]

        if taxable_income > bracket_min:
            if bracket_max is None:
                # Top bracket, tax all remaining income
                amount_taxable = taxable_income - bracket_min
            else:
                amount_taxable = min(taxable_income - bracket_min, bracket_max - bracket_min)
            tax_owed += amount_taxable * rate
    return tax_owed


def calculate_total_withholding(w2s, ints, necs):
    """Sum all federal tax withheld."""
    total_withheld = sum(w2.get("federal_tax_withheld", 0.0) for w2 in w2s)
    total_withheld += sum(i.get("federal_tax_withheld", 0.0) for i in ints)
    total_withheld += sum(n.get("federal_tax_withheld", 0.0) for n in necs)
    return total_withheld


def calculate_taxes(taxpayer_data, year):
    """
    Main function to calculate taxes.
    Expects taxpayer_data dict with keys: 'w2s', '1099ints', '1099necs', 'filing_status'.
    """
    w2s = taxpayer_data.get("w2s", [])
    ints = taxpayer_data.get("1099ints", [])
    necs = taxpayer_data.get("1099necs", [])
    filing_status = taxpayer_data.get("taxpayer", {}).get("filing_status")

    # --- Step 1: Gross Income ---
    wages, interest_income, self_employment_income, gross_income = calculate_gross_income(w2s, ints, necs)

    # --- Step 2: Taxable Income ---
    taxable_income, standard_deduction = calculate_taxable_income(gross_income, filing_status, year)

    # --- Step 3: Tax Owed ---
    tax_owed = calculate_tax_owed(taxable_income, filing_status, year)

    # --- Step 4: Federal Withholding ---
    total_withheld = calculate_total_withholding(w2s, ints, necs)

    # --- Step 5: Refund / Amount Due ---
    refund_or_amount_due = total_withheld - tax_owed

    # --- Step 6: Return structured summary ---
    return {
        "gross_income": round(gross_income, 2),
        "wages": round(wages, 2),
        "interest_income": round(interest_income, 2),
        "self_employment_income": round(self_employment_income, 2),
        "standard_deduction": round(standard_deduction, 2),
        "taxable_income": round(taxable_income, 2),
        "tax_owed": round(tax_owed, 2),
        "federal_tax_withheld": round(total_withheld, 2),
        "refund_or_amount_due": round(refund_or_amount_due, 2)
    }



# Example usage:
if __name__ == "__main__":
    # Replace this with actual data from frontend
    example_data = {}  # your JSON structure
    result = calculate_taxes(example_data, "2024")
    print(json.dumps(result, indent=2))
