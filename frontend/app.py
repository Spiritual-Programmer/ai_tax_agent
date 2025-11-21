import datetime
import os
import sys
import streamlit as st

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.extract_w2 import extract_all_w2
from backend.extract_1099_int import extract_1099_int
from backend.extract_1099_nec import extract_1099_nec
from backend.tax_return import (
    add_w2_to_tax_return,
    add_1099_int_to_tax_return,
    add_1099_nec_to_tax_return,
    init_tax_return,
)
from config import FORM_1040_TEMPLATE_PATH
from backend.calculate_taxes import calculate_taxes
from backend.generate_1040 import fill_1040_pdf



st.title("AI Tax Agent")
st.write("File your taxes instantly!")

# ------------------------
# Helper Functions
# ------------------------

def add_additional_person(person_type, unique_key):
    """Add spouse or dependent info."""
    with st.expander(f"Enter {person_type} Information"):
        first_name = st.text_input(f"{person_type} First Name", key=f"{unique_key}_first_name").capitalize()
        last_name = st.text_input(f"{person_type} Last Name", key=f"{unique_key}_last_name").capitalize()
        ssn = st.text_input(f"{person_type} SSN", key=f"{unique_key}_ssn", type="password").replace("-", "").replace(" ", "")
        
        min_dob = datetime.date(1900, 1, 1)
        max_dob = datetime.date.today()
        dob = st.date_input(f"{person_type} Date of Birth", key=f"{unique_key}_dob", min_value=min_dob, max_value=max_dob, value=min_dob)

        extra_fields = {}
        if person_type == "Spouse":
            is_blind = st.radio(f"Is your {person_type} blind?", ["No", "Yes"], index=None)
            extra_fields["is_blind"] = is_blind.lower() if is_blind else None
        elif "Dependent" in person_type:
            extra_fields["relationship"] = st.text_input(f"{person_type} Relationship to you", key=f"{unique_key}_relationship").strip()

        # Use dob_valid instead of address_valid
        if first_name and last_name and ssn and dob_valid(dob):
            return {**{"first_name": first_name, "last_name": last_name, "ssn": ssn, "date_of_birth": str(dob)}, **extra_fields}

    return None


def address_valid(address):
    return address is not None and len(address.strip()) > 0

def dob_valid(dob):
    return dob <= datetime.date.today()

def get_taxpayer_info():
    st.subheader("Taxpayer Information")
    first_name = st.text_input("First Name").capitalize()
    last_name = st.text_input("Last Name").capitalize()
    ssn = st.text_input("SSN", type="password").replace("-", "").replace(" ", "")
    address = st.text_area("Address")

    min_dob = datetime.date(1900, 1, 1)
    max_dob = datetime.date.today()
    date_of_birth = st.date_input("Date of Birth", min_value=min_dob, max_value=max_dob, value=min_dob)

    filing_status = st.selectbox(
        "Filing Status",
        ["Single", "Married filing jointly", "Married filing separately",
         "Head of household", "Qualifying surviving spouse"],
        index=None,
        placeholder="Select your filing status"
    )
    filing_status_normalized = filing_status.lower().replace(" ", "_") if filing_status else None

    # Spouse info appears immediately after filing status if needed
    spouse_info = {}
    if filing_status_normalized in ["married_filing_jointly", "married_filing_separately"]:
        spouse_info = add_additional_person("Spouse", "spouse")

    is_blind = st.radio("Are you blind?", ["No", "Yes"], index=None)
    is_blind = is_blind.lower() if is_blind else None

    received_or_sold_digital_asset = st.radio(
        "At any time during 2024, did you receive, sell, or exchange digital assets?",
        ["No", "Yes"],
        index=None
    )
    received_or_sold_digital_asset = received_or_sold_digital_asset.lower() if received_or_sold_digital_asset else None

    return {
        "first_name": first_name,
        "last_name": last_name,
        "ssn": ssn,
        "address": address,
        "date_of_birth": str(date_of_birth),
        "filing_status": filing_status_normalized,
        "is_blind": is_blind,
        "received_or_sold_digital_asset": received_or_sold_digital_asset,
        "spouse_info": spouse_info
    }

def get_dependents():
    dependents = []
    has_dependents = st.radio("Do you have dependents?", ["Yes", "No"], index=None)
    if has_dependents:
        has_dependents_lower = has_dependents.lower()
        if has_dependents_lower == "yes":
            num_deps = st.number_input("How many dependents?", 1, 18, 1)
            for i in range(num_deps):
                dep_info = add_additional_person(f"Dependent {i+1}", f"dep_{i}")
                if dep_info:
                    dependents.append(dep_info)
        return dependents, has_dependents_lower
    return dependents, None

def upload_files(label, file_types=["pdf"]):
    return st.file_uploader(label, type=file_types, accept_multiple_files=True)

def validate_required_fields(taxpayer_profile, uploaded_w2, uploaded_1099_int, uploaded_1099_nec):
    missing_fields = []

    # Taxpayer info
    if not taxpayer_profile.get("first_name"):
        missing_fields.append("Taxpayer First Name")
    if not taxpayer_profile.get("last_name"):
        missing_fields.append("Taxpayer Last Name")
    if not taxpayer_profile.get("ssn"):
        missing_fields.append("Taxpayer SSN")
    if not taxpayer_profile.get("address") or not address_valid(taxpayer_profile.get("address")):
        missing_fields.append("Taxpayer Address")
    if not taxpayer_profile.get("filing_status"):
        missing_fields.append("Filing Status")
    dob = datetime.datetime.strptime(taxpayer_profile.get("date_of_birth"), "%Y-%m-%d").date()
    if not dob_valid(dob):
        missing_fields.append("Date of Birth cannot be in the future")
    if taxpayer_profile.get("is_blind") is None:
        missing_fields.append("Are you blind?")
    if taxpayer_profile.get("received_or_sold_digital_asset") is None:
        missing_fields.append("Digital Asset Question")

    # Spouse validation if filing status requires
    spouse = taxpayer_profile.get("spouse_info")
    if taxpayer_profile.get("filing_status") in ["married_filing_jointly", "married_filing_separately"]:
        if not spouse or not spouse.get("first_name") or not spouse.get("last_name") or not spouse.get("ssn"):
            missing_fields.append("Spouse Information")

    # Dependents validation
    if taxpayer_profile.get("has_dependents") == "yes" and not taxpayer_profile.get("dependents"):
        missing_fields.append("Dependents Information")

    # File uploads
    if not (uploaded_w2 or uploaded_1099_int or uploaded_1099_nec):
        missing_fields.append("At least one file upload (W-2, 1099-INT, 1099-NEC)")

    return missing_fields

# ------------------------
# Main Execution
# ------------------------

taxpayer_profile = get_taxpayer_info()

# Dependents
dependents, has_dependents = get_dependents()
taxpayer_profile["dependents"] = dependents
taxpayer_profile["has_dependents"] = has_dependents

# File uploads
uploaded_w2_files = upload_files("Upload your W-2 PDFs (multiple allowed)")
uploaded_1099_int_files = upload_files("Upload your 1099-INT PDFs (multiple allowed)")
uploaded_1099_nec_files = upload_files("Upload your 1099-NEC PDFs (multiple allowed)")

if st.button("Continue"):
    missing_fields = validate_required_fields(
        taxpayer_profile, uploaded_w2_files, uploaded_1099_int_files, uploaded_1099_nec_files
    )

    if missing_fields:
        st.error(f"Missing required fields: {', '.join(missing_fields)}")
        st.stop()

    # Initialize tax return
    tax_return = init_tax_return()

    # Process W2s
    if uploaded_w2_files:
        w2_forms = extract_all_w2(uploaded_w2_files)
        for form in w2_forms:
            add_w2_to_tax_return(tax_return, form)

    # Process 1099-INTs
    if uploaded_1099_int_files:
        forms_1099_int = extract_1099_int(uploaded_1099_int_files)
        for form in forms_1099_int:
            add_1099_int_to_tax_return(tax_return, form)

    # Process 1099-NECs
    if uploaded_1099_nec_files:
        forms_1099_nec = extract_1099_nec(uploaded_1099_nec_files)
        for form in forms_1099_nec:
            add_1099_nec_to_tax_return(tax_return, form)

    # Combine final tax data
    final_tax_data = {
        "taxpayer": taxpayer_profile,
        "w2s": tax_return.get("w2s", []),
        "1099ints": tax_return.get("1099ints", []),
        "1099necs": tax_return.get("1099necs", []),
        "totals": tax_return.get("totals", {})
    }

    # st.success("Data collected and parsed successfully!")
    # st.subheader("Final Tax Data")
    # st.json(final_tax_data)

    # Calculate Taxes
    tax_summary = calculate_taxes(final_tax_data, "2024")  # replace "2024" with actual year if dynamic

    # st.subheader("Tax Calculation Summary")
    # st.json(tax_summary)

    st.subheader("Generate 1040 Form PDF")
    try:
        # Create PDF in memory
        pdf_bytes = fill_1040_pdf(
        file_path=FORM_1040_TEMPLATE_PATH,
        taxpayer_profile=taxpayer_profile,
        tax_summary=tax_summary
        )

        st.success("1040 PDF generated successfully!")

        # Provide download button
        st.download_button(
        label="Download 1040 PDF",
        data=pdf_bytes,
        file_name="1040_filled.pdf",
        mime="application/pdf"
        )

    except Exception as e:
        st.error(f"Failed to generate 1040 PDF: {e}")
