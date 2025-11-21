# parsers/parse_1099_nec.py
from typing import List, Dict, Any
import tempfile
import os
import re
import pymupdf4llm


def _process_single_1099_nec(pdf_file) -> dict:
    """
    Extract data from a single 1099-NEC PDF file using the existing regex patterns.
    Returns a dictionary compatible with tax_return architecture.
    """
    if pdf_file is None:
        return {}

    pdf_bytes = pdf_file.read()
    temp_filepath = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(pdf_bytes)
            temp_filepath = tmp_file.name

        text = pymupdf4llm.to_markdown(temp_filepath)

        # Standardized dictionary
        result = {
            "source_file": pdf_file.name,
            "payer_name": None,
            "recipient_address": None,
            "nonemployee_compensation": 0.0,  # Box 1
            "federal_tax_withheld": 0.0,      # Box 4
            "state_tax_withheld": 0.0,        # Box 5
            "state_income": 0.0               # Box 7
        }

        # --- Apply your regex patterns ---
        # Payer name
        payer = re.search(r'\*\*([A-Za-z0-9\s\.,&\'-]+(?:Inc\.|LLC|Corp|N\.A\.)[,\.]?)\*\*', text)
        if payer:
            result["payer_name"] = payer.group(1).strip()

        # Recipient address
        recip = re.search(r"foreign postal code[<br>\n\|]*\*\*([^*]+)\*\*[<br>\n\|]*\*\*([^*]+)\*\*", text)
        if recip:
            result["recipient_address"] = f"{recip.group(1)}, {recip.group(2)}"

        # Box 1
        box1 = re.search(r"\*\*1\s*\*\*Nonemployee compensation[<br>\n\$\|]*\*\*([0-9,]+\.?\d*)\*\*", text)
        if box1:
            result["nonemployee_compensation"] = float(box1.group(1).replace(',', ''))

        # Box 4
        box4 = re.search(r"\*\*4\s*\*\*Federal income tax withheld[<br>\n\$\|]*\*\*([0-9,]+\.?\d*)\*\*", text)
        if box4:
            result["federal_tax_withheld"] = float(box4.group(1).replace(',', ''))

        # Box 5
        box5 = re.search(r"\*\*5\s*\*\*State tax withheld[<br>\n\$\|]*\*\*([0-9,]+\.?\d*)\*\*", text)
        if box5:
            result["state_tax_withheld"] = float(box5.group(1).replace(',', ''))

        # Box 7
        box7 = re.search(r"\*\*7\s*\*\*State income[<br>\n\$\|]*\*\*([0-9,]+\.?\d*)\*\*", text)
        if box7:
            result["state_income"] = float(box7.group(1).replace(',', ''))

        return result

    finally:
        if temp_filepath and os.path.exists(temp_filepath):
            os.unlink(temp_filepath)


def extract_1099_nec(pdf_files: List[Any]) -> List[Dict[str, Any]]:
    """
    Process a list of 1099-NEC files and return list of standardized dictionaries.
    """
    if not pdf_files:
        return []

    all_extracted_data = []

    for file in pdf_files:
        try:
            data = _process_single_1099_nec(file)
            all_extracted_data.append(data)
        except Exception as e:
            all_extracted_data.append({
                "source_file": file.name,
                "error": f"Failed to extract data: {e}"
            })

    return all_extracted_data
