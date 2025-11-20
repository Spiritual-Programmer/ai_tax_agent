from pypdf import PdfReader, PdfWriter
import io # for in-memory handling

def discover_pdf_field_info(pdf_path):
    reader = PdfReader(pdf_path)
    fields = reader.get_fields()
    
    print("=== PAGE 1 CHECKBOXES (Filing Status) ===")
    for field_name, field_info in fields.items():
        # Look for checkboxes on Page 1
        if '/FT' in field_info and field_info['/FT'] == '/Btn' and 'Page1' in field_name:
            states = field_info.get('/_States_', [])
            current_value = field_info.get('/V', 'Not set')
            print(f"\nField: {field_name}")
            print(f"  States: {states}")
            print(f"  Current Value: {current_value}")
    # print("=== Form 1040 Fields ===")
    # for field_name, field_info in fields.items():
    #     print(f"{field_name} : {field_info}")
    
    return fields

def fill_1040_pdf (file_path, w2_data, taxpayer_profile):
    writer = PdfWriter(clone_from=file_path)
    
    # Fill name & ssn
    field_data = {
        'topmostSubform[0].Page1[0].f1_04[0]': w2_data["employee"]["first_name"],
        'topmostSubform[0].Page1[0].f1_05[0]': w2_data["employee"]["last_name"],
        'topmostSubform[0].Page1[0].f1_06[0]': w2_data["employee"]["ssn"].replace("-",""),
    }

    # Filing status section
    if taxpayer_profile["filing_status"] == "single":
        field_data['topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[0]'] ='/1'
    elif taxpayer_profile["filing_status"] == "head_of_household":
        field_data['topmostSubform[0].Page1[0].c1_3[0]'] = '/2' #checkmark for hoh
    elif taxpayer_profile["filing_status"] == "married_filing_jointly":
        field_data['topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[1]'] = '/3'
        field_data['topmostSubform[0].Page1[0].f1_07[0]'] = taxpayer_profile['spouse_info']['first_name'] #first name
        field_data['topmostSubform[0].Page1[0].f1_08[0]'] = taxpayer_profile['spouse_info']['last_name'] #last name
        field_data['topmostSubform[0].Page1[0].f1_09[0]'] = taxpayer_profile['spouse_info']['ssn'] #ssn
    elif taxpayer_profile["filing_status"] == "married_filing_separately":
        field_data['topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[2]'] = '/4'
        field_data['topmostSubform[0].Page1[0].f1_18[0]'] = f'{taxpayer_profile['spouse_info']['first_name']} {taxpayer_profile['spouse_info']['last_name']}'
    elif taxpayer_profile["filing_status"] == "qualifying_surviving_spouse":
        field_data['topmostSubform[0].Page1[0].c1_3[1]'] = '/5'
    else:
        field_data['topmostSubform[0].Page1[0].c1_4[0]'] = '/1'

    # Digital assets
    if taxpayer_profile["received_or_sold_digital_asset"] == "yes":
        field_data['topmostSubform[0].Page1[0].c1_5[0]'] ='/1'
    else:
        field_data['topmostSubform[0].Page1[0].c1_5[1]'] ='/2'

    #  Taxpayer Age & blindness
    if taxpayer_profile["date_of_birth"] <= "1960-01-02": 
        field_data['topmostSubform[0].Page1[0].c1_9[0]'] = '/1'  
    if taxpayer_profile["is_blind"] == "yes": 
        field_data['topmostSubform[0].Page1[0].c1_10[0]'] = '/1'
    
     #  Spouse Age & blindness
    if taxpayer_profile["filing_status"] == "married_filing_jointly" or taxpayer_profile["filing_status"] == "married_filing_separately":
        if taxpayer_profile["spouse_info"]["date_of_birth"] <= "1960-01-02": 
            field_data['topmostSubform[0].Page1[0].c1_11[0]'] = '/1'  
        if taxpayer_profile["spouse_info"]["is_blind"] == "yes": 
            field_data['topmostSubform[0].Page1[0].c1_12[0]'] = '/1'
    
    # Dependents
    # if taxpayer_profile["has_dependents"] == "yes":
    #     for 
    
    # Income Section
    field_data = {
        'topmostSubform[0].Page1[0].f1_32[0]': w2_data["wages_and_taxes"]["box_1_wages"],
    }



    writer.update_page_form_field_values(writer.pages[0],field_data)
    writer.update_page_form_field_values(writer.pages[1],field_data)
    
    # # --- START DOWNLOADABLE FILE LOGIC ---
    # # 1. Create an in-memory buffer (BytesIO)
    # output_buffer = io.BytesIO()
    
    # # 2. Write the PDF content directly to the buffer
    # writer.write(output_buffer)
    
    # # 3. Get the binary content and return it
    # return output_buffer.getvalue()
    # # --- END DOWNLOADABLE FILE LOGIC ---

    with open('output.pdf', 'wb') as f:
        writer.write(f)

#discover_pdf_field_info('./backend/form_1040_template.pdf')