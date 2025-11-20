import datetime
import os
import sys
import streamlit as st
# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.extract_w2 import parse_w2
from backend.calculate_taxes import calculate_taxes
from backend.generate_1040 import fill_1040_pdf

def add_additional_person(person_type, unique_key):
    # Add dependent or spouse information
    with st.expander(f'Enter {person_type} information'):
        first_name = st.text_input(
            f"{person_type} first name", 
            key=f"{unique_key}_first_name"
        ).capitalize()
        last_name = st.text_input(
            f"{person_type} last name", 
            key=f"{unique_key}_last_name"
        ).capitalize()
        person_ssn = st.text_input(
            f"{person_type} SSN", 
            key=f"{unique_key}_ssn",
            max_chars=11, # Max length for ###-##-####
            type="password", # Masks the input for security
            help="Your SSN is required for accurate tax filing. It will be masked for security."
        ).replace("-","").replace(" ","")
        # Define the date bounds
        # Set the earliest date to January 1, 1900
        min_dob = datetime.date(1900, 1, 1)
        # Set the latest date to today
        max_dob = datetime.date.today() 
        person_dob = st.date_input(
            f"{person_type} date of birth", 
            key=f"{unique_key}_dob",value=min_dob, min_value=min_dob, max_value=max_dob
        )
        is_blind = ""
        if person_type == "Spouse":
            is_blind = st.radio(f"Is your {person_type} blind?", ["No", "Yes"]).lower()
        relationship = ""
        if "Dependent" in person_type:
            relationship = st.text_input(
            f"{person_type} Relationship to you", 
            key=f"{unique_key}_relationship"
        )
        
        # Check if required fields are filled
        if first_name and last_name and person_ssn:
            return {
                "first_name": first_name,
                "last_name": last_name,
                "ssn": person_ssn,
                "date_of_birth": str(person_dob),
                "is_blind": is_blind,
                "relatoinship": relationship,
            }
    
    return None

st.title("AI Tax Agent")
st.write("File your taxes instantly!")

uploaded_w2_file = st.file_uploader(
    "Upload your W-2 PDF",
    type=["pdf"],
    accept_multiple_files=False
)

filing_status = st.selectbox(
    "Filing status",
    ["Single", "Married filing jointly", "Married filing separately",
     "Head of household", "Qualifying surviving spouse"],
    index=None,
    placeholder="Select your filing status"
)
filing_status = filing_status.lower().replace(" ", "_") if filing_status else None

spouse_info = {}
if filing_status == "married_filing_jointly" or filing_status == "married_filing_separately":
    spouse_info = add_additional_person("Spouse", "spouse")


# Define the date bounds
# Set the earliest date to January 1, 1900
min_dob = datetime.date(1900, 1, 1)
# Set the latest date to today
max_dob = datetime.date.today() 
date_of_birth = st.date_input("Your Date of Birth", value=min_dob, min_value=min_dob, max_value=max_dob)

has_dependents = st.radio("Do you have dependents?", ["No", "Yes"]).lower()



dependents = []
if has_dependents == "yes":
    num_deps = st.number_input("How many dependents?", 1, 18, 1)
    
    for i in range(num_deps):
        dep_info = add_additional_person(f"Dependent {i+1}", f"dep_{i}")
        if dep_info:
            dependents.append(dep_info)

received_or_sold_digital_asset = st.radio("At any time during 2024, did you: (a) receive (as a "
"reward, award, or payment for property or services); or (b) sell, exchange, or otherwise dispose "
"of a digital asset (or a financial interest in a digital asset)? (See instructions.)", ["No", "Yes"]).lower()

is_blind = st.radio("Are you blind?", ["No", "Yes"]).lower()


if st.button("Continue"):
    if not filing_status:
        st.error("Please select a filing status.")
        st.stop()
    if uploaded_w2_file is None:
        st.error("Please upload your W-2 PDF.")
        st.stop()

    taxpayer_profile = {
        "filing_status": filing_status,
        "date_of_birth": str(date_of_birth),
        "dependents": dependents,
        "has_dependents": has_dependents,
        "spouse_info": spouse_info,
        'received_or_sold_digital_asset': received_or_sold_digital_asset,
        "is_blind": is_blind
    }

    w2_data = parse_w2(uploaded_w2_file)

    # Show collected data
    st.success("Data collected successfully!")
    st.subheader("Taxpayer Profile")
    st.json(taxpayer_profile)

    st.subheader("Parsed W-2 Data")
    st.json(w2_data)
    year = "2024"
    gross_income = calculate_taxes(w2_data, taxpayer_profile, year)
    st.write(gross_income)
    fill_1040_pdf('./backend/form_1040_template.pdf',w2_data,taxpayer_profile)
