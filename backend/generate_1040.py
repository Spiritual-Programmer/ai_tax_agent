from io import BytesIO
import re
from pypdf import PdfReader, PdfWriter

def parse_address(address_str):
    """
    Safe, regex-free U.S. address parser with proper capitalization.
    """

    if not address_str:
        return {
            "street": "",
            "apt": "",
            "city": "",
            "state": "",
            "zip": ""
        }

    addr = address_str.strip()
    parts = [p.strip() for p in addr.split(",")]

    if len(parts) < 3:
        # Not enough comma-separated components → fallback
        return {
            "street": addr.title(),
            "apt": "",
            "city": "",
            "state": "",
            "zip": ""
        }

    street_section = parts[0]
    city = parts[-2]
    state_zip = parts[-1].split()

    # Default state/zip values
    state = ""
    zipcode = ""

    if len(state_zip) >= 2:
        state = state_zip[0].upper()
        zipcode = state_zip[1]

    # Detect apt/unit number
    apt = ""
    street = street_section

    for keyword in ["apt", "unit", "suite", "ste", "#"]:
        if keyword in street_section.lower():
            tokens = street_section.split()
            for i, token in enumerate(tokens):
                if keyword in token.lower():
                    apt = " ".join(tokens[i:])
                    street = " ".join(tokens[:i])
                    break

    # Capitalize properly
    street = street.title().strip()
    apt = apt.title().strip()
    city = city.title().strip()

    return {
        "street": street,
        "apt": apt,
        "city": city,
        "state": state.strip().upper(),
        "zip": zipcode.strip()
    }


    
def discover_pdf_field_info(pdf_path):
    """
    Discover all fields in the PDF, and print checkboxes separately.
    """
    reader = PdfReader(pdf_path)
    fields = reader.get_fields()
    
    print("=== PAGE 1 CHECKBOXES (Filing Status) ===")
    for field_name, field_info in fields.items():
        if '/FT' in field_info and field_info['/FT'] == '/Btn' and 'Page1' in field_name:
            states = field_info.get('/_States_', [])
            current_value = field_info.get('/V', 'Not set')
            print(f"\nField: {field_name}")
            print(f"  States: {states}")
            print(f"  Current Value: {current_value}")
    
    print("\n=== ALL PDF FIELDS ===")
    counter = 1
    for field_name, field_info in fields.items():
        field_type = field_info.get('/FT', 'Unknown')
        current_value = field_info.get('/V', 'Not set')
        print(f"{counter}. Field: {field_name}")
        print(f"    Type: {field_type}")
        print(f"    Current Value: {current_value}")
        counter += 1
    
    return fields

def fill_pdf_fields_with_unique_numbers(pdf_path, output_path):
    """
    Fill all form fields with unique numbers for mapping purposes.
    """
    reader = PdfReader(pdf_path)
    writer = PdfWriter(clone_from=pdf_path)

    fields = reader.get_fields()
    counter = 1
    field_data = {}
    
    for field_name, field_info in fields.items():
        # Skip checkboxes (we usually handle separately)
        if '/FT' in field_info and field_info['/FT'] == '/Btn':
            continue
        field_data[field_name] = str(counter)
        counter += 1
    
    # Update all pages
    for page in writer.pages:
        writer.update_page_form_field_values(page, field_data)
    
    writer.write(output_path)
    print(f"All fields filled with unique numbers and saved to {output_path}")

def fill_1040_pdf(file_path, taxpayer_profile, tax_summary):
    writer = PdfWriter(clone_from=file_path)

    # ------------------------
    # 1. Name & SSN
    # ------------------------
    field_data = {
        'topmostSubform[0].Page1[0].f1_04[0]': taxpayer_profile["first_name"],
        'topmostSubform[0].Page1[0].f1_05[0]': taxpayer_profile["last_name"],
        'topmostSubform[0].Page1[0].f1_06[0]': taxpayer_profile["ssn"],
    }
    # Address
    address_parts = parse_address(taxpayer_profile["address"])
    field_data["topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_10[0]"] = address_parts["street"]
    field_data["topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_11[0]"] = address_parts["apt"]
    field_data["topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_12[0]"] = address_parts["city"]
    field_data["topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_13[0]"] = address_parts["state"]
    field_data["topmostSubform[0].Page1[0].Address_ReadOrder[0].f1_14[0]"] = address_parts["zip"]


    # ------------------------
    # 2. Filing Status Section
    # ------------------------
    fs = taxpayer_profile.get("filing_status")
    if fs == "single":
        field_data['topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[0]'] = '/1'
    elif fs == "head_of_household":
        field_data['topmostSubform[0].Page1[0].c1_3[0]'] = '/2'
    elif fs == "married_filing_jointly":
        field_data['topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[1]'] = '/3'
        field_data['topmostSubform[0].Page1[0].f1_07[0]'] = taxpayer_profile['spouse_info']['first_name']
        field_data['topmostSubform[0].Page1[0].f1_08[0]'] = taxpayer_profile['spouse_info']['last_name']
        field_data['topmostSubform[0].Page1[0].f1_09[0]'] = taxpayer_profile['spouse_info']['ssn']
    elif fs == "married_filing_separately":
        field_data['topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[2]'] = '/4'
        field_data['topmostSubform[0].Page1[0].f1_18[0]'] = f"{taxpayer_profile['spouse_info']['first_name']} {taxpayer_profile['spouse_info']['last_name']}"
    elif fs == "qualifying_surviving_spouse":
        field_data['topmostSubform[0].Page1[0].c1_3[1]'] = '/5'
    else:
        field_data['topmostSubform[0].Page1[0].c1_4[0]'] = '/1'

    # ------------------------
    # 3. Digital Assets
    # ------------------------
    if taxpayer_profile.get("received_or_sold_digital_asset") == "yes":
        field_data['topmostSubform[0].Page1[0].c1_5[0]'] = '/1'
    else:
        field_data['topmostSubform[0].Page1[0].c1_5[1]'] = '/2'

    # ------------------------
    # 4. Taxpayer Age & Blindness
    # ------------------------
    if taxpayer_profile.get("date_of_birth") <= "1960-01-02": 
        field_data['topmostSubform[0].Page1[0].c1_9[0]'] = '/1'  
    if taxpayer_profile.get("is_blind") == "yes": 
        field_data['topmostSubform[0].Page1[0].c1_10[0]'] = '/1'
    
    # ------------------------
    # 5. Spouse Age & Blindness
    # ------------------------
    if fs in ["married_filing_jointly", "married_filing_separately"]:
        spouse = taxpayer_profile.get("spouse_info", {})
        if spouse.get("date_of_birth") <= "1960-01-02": 
            field_data['topmostSubform[0].Page1[0].c1_11[0]'] = '/1'  
        if spouse.get("is_blind") == "yes": 
            field_data['topmostSubform[0].Page1[0].c1_12[0]'] = '/1'

    # ------------------------
    # 6. Dependents
    # ------------------------
    field_data['needs_dependents_fields'] = "needs field location form 1040"

    # ------------------------
    # 7. Income Section (from tax_summary)
    # ------------------------
    field_data.update({
        'topmostSubform[0].Page1[0].f1_32[0]': round(tax_summary.get("wages", 0), 2),
        'topmostSubform[0].Page1[0].f1_41[0]': round(tax_summary.get("wages", 0), 2),
        'topmostSubform[0].Page1[0].f1_43[0]': round(tax_summary.get("interest_income", 0), 2),
        'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_53[0]': round(tax_summary.get("self_employment_income", 0), 2),
        'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_54[0]': round(tax_summary.get("gross_income", 0), 2),
        'topmostSubform[0].Page1[0].Line4a-11_ReadOrder[0].f1_56[0]': round(tax_summary.get("gross_income", 0), 2), #agi
        'topmostSubform[0].Page1[0].f1_57[0]': round(tax_summary.get("standard_deduction", 0), 2),
        'topmostSubform[0].Page1[0].f1_59[0]': round(tax_summary.get("standard_deduction", 0), 2), # adding standard and business deductions
        'topmostSubform[0].Page1[0].f1_60[0]': round(tax_summary.get("taxable_income", 0), 2),
        'topmostSubform[0].Page2[0].f2_02[0]': round(tax_summary.get("tax_owed", 0), 2),
        'topmostSubform[0].Page2[0].f2_04[0]': round(tax_summary.get("tax_owed", 0), 2), #18
        'topmostSubform[0].Page2[0].f2_10[0]': round(tax_summary.get("tax_owed", 0), 2), # 24
        'topmostSubform[0].Page2[0].f2_14[0]': round(tax_summary.get("federal_tax_withheld", 0), 2), #25d
        'topmostSubform[0].Page2[0].f2_22[0]': round(tax_summary.get("federal_tax_withheld", 0), 2), #33
    })

    if tax_summary.get("federal_tax_withheld") > tax_summary.get("tax_owed"):
        field_data.update({'topmostSubform[0].Page2[0].f2_23[0]': round(tax_summary.get("refund_or_amount_due", 0), 2)}) #34
    else:
        field_data.update({'topmostSubform[0].Page2[0].f2_28[0]': abs(round(tax_summary.get("refund_or_amount_due", 0), 2))}) #37


    # ------------------------
    # 8. Write to PDF
    # ------------------------
    writer.update_page_form_field_values(writer.pages[0], field_data)
    writer.update_page_form_field_values(writer.pages[1], field_data)

    # ------------------------
    # 9. Return PDF as bytes for Streamlit download
    # ------------------------
    pdf_buffer = BytesIO()
    writer.write(pdf_buffer)
    pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()
    return pdf_bytes