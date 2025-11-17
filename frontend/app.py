import datetime
import os
import sys
import streamlit as st
# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.extract_w2 import parse_w2
from backend.calculate_taxes import calculate_taxes

st.title("AI Tax Agent")
st.write("File your taxes instantly!")

filing_status = st.selectbox(
    "Filing status",
    ["Single", "Married filing jointly", "Married filing separately",
     "Head of household", "Qualifying surviving spouse"],
    index=None,
    placeholder="Select your filing status"
)
filing_status = filing_status.lower().replace(" ", "_") if filing_status else None

default_date = datetime.date(1990, 1, 1)
date_of_birth = st.date_input("Date of Birth", value=default_date)

has_dependents = st.radio("Do you have dependents?", ["no", "yes"])

dependents = []
if has_dependents == "yes":
    with st.expander("Enter dependent information"):
        dep_name = st.text_input("Dependent full name")
        dep_ssn = st.text_input("Dependent SSN")
        dep_dob = st.date_input("Dependent DOB")

        if dep_name and dep_ssn:
            dependents.append({
                "name": dep_name,
                "ssn": dep_ssn,
                "dob": str(dep_dob)
            })

uploaded_w2_file = st.file_uploader(
    "Upload your W-2 PDF",
    type=["pdf"],
    accept_multiple_files=False
)

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
        "has_dependents": has_dependents
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
