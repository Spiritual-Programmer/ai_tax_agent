import json

with open("./backend/tax_config.json", 'r') as file:
    tax_data = json.load(file)

def calculate_taxes(w2_data, taxpayer_profile, year):
    year_data = tax_data[year]
    standard_deduction = year_data["standard_deductions"]

    # W2 Data
    wages = w2_data["wages_and_taxes"]["box_1_wages"] 
    federal_tax_witheld = w2_data["wages_and_taxes"]["box_2_federal_tax_withheld"]
    ss_wages = w2_data["wages_and_taxes"]["box_3_ss_wages"]
    ss_tax_withheld = w2_data["wages_and_taxes"]["box_4_ss_tax_withheld"]
    medicare_wages = w2_data["wages_and_taxes"]["box_5_medicare_wages"]
    medicare_tax_withheld = w2_data["wages_and_taxes"]["box_6_medicare_tax_withheld"]
    ss_tips = w2_data["wages_and_taxes"]["box_7_ss_tips"]

    
    gross_income = wages  #update
    taxable_income = gross_income - standard_deduction[taxpayer_profile["filing_status"]]

    brackets = year_data['tax_brackets'][taxpayer_profile["filing_status"]]

    tax_owed = 0
    for bracket in brackets:
        if taxable_income >= bracket["min"]:
            if bracket["max"] is None:
                amount_taxable_at_bracket = taxable_income - bracket["min"]
            elif taxable_income > bracket["max"]:
                amount_taxable_at_bracket = bracket["max"] - bracket["min"] 
            else:
                amount_taxable_at_bracket = taxable_income - bracket["min"]
            tax_owed += amount_taxable_at_bracket * bracket["rate"]
    
    
    difference = federal_tax_witheld - tax_owed

    return difference
