import json

with open("./backend/tax_config.json", 'r') as file:
    tax_data = json.load(file)

def calculate_taxes(w2_data, taxpayer_profile, year):
    year_data = tax_data[year]
    standard_deduction = year_data["standard_deductions"]

    gross_income = w2_data["wages_and_taxes"]["box_1_wages"]
    taxable_income = gross_income - standard_deduction[taxpayer_profile["filing_status"]]

    brackets = year_data['tax_brackets'][taxpayer_profile["filing_status"]]

    tax = 0
    for bracket in brackets:
        if taxable_income >= bracket["min"]:
            if bracket["max"] is None:
                amount_taxable_at_bracket = taxable_income - bracket["min"]
            elif taxable_income > bracket["max"]:
                amount_taxable_at_bracket = bracket["max"] - bracket["min"] 
            else:
                amount_taxable_at_bracket = taxable_income - bracket["min"]
            tax += amount_taxable_at_bracket * bracket["rate"]

    return tax
