from typing import List, Dict, Any
import io 
import tempfile # For creating temporary files
import os 
import pymupdf4llm
import re
from .w2_patterns import * 

def _process_single_1099_int(pdf_file) -> dict:
    if pdf_file is None:
        return {}
        
    pdf_bytes = pdf_file.read()
    temp_filepath = None
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(pdf_bytes)
            temp_filepath = tmp_file.name
        
        text = pymupdf4llm.to_markdown(temp_filepath)
        
        # --- Standardized dictionary ---
        result = {
            "source_file": pdf_file.name,

            "payer_name": None,
            "payer_tin": None,
            "recipient_name": None,
            "recipient_tin": None,

            # ----- Standard IRS usable fields -----
            "interest_income": 0.0,          # box 1
            "early_withdrawal_penalty": 0.0, # box 2 (usually absent)
            "federal_tax_withheld": 0.0,     # box 4
            "state": None,                   # box 16
            "state_tax_withheld": 0.0        # box 17
        }
        
        # --- Extraction logic (unchanged) ---
        
        payer = re.search(r'202[3-5]\n(.+?)(?=\n\d)', text, re.DOTALL)
        if payer:
            lines = payer.group(1).strip().split('\n')
            result["payer_name"] = lines[0] if lines else None
        
        tins = re.search(r'(\d{2}-\d{7})(\d{3}-\d{2}-\d{4})', text)
        if tins:
            result["payer_tin"] = tins.group(1)
            result["recipient_tin"] = tins.group(2)
        
        recip = re.search(r'\d{3}-\d{2}-\d{4}\n([A-Z][a-z]+ [A-Z][a-z]+)', text)
        if recip:
            result["recipient_name"] = recip.group(1)
        
        amounts = re.findall(r'(\d+\.\d{2})', text)
        non_zero = [float(a) for a in amounts if float(a) > 1.0]
        if non_zero:
            result["interest_income"] = non_zero[0]

        # Federal withholding: if found anywhere (box 4)
        fed_withheld = re.search(r'Federal tax withheld.*?(\d+\.\d{2})', text)
        if fed_withheld:
            result["federal_tax_withheld"] = float(fed_withheld.group(1))

        # State tax withheld — your previous logic
        small_amounts = [float(a) for a in amounts if 0 < float(a) <= 10]
        if small_amounts:
            result["state_tax_withheld"] = small_amounts[-1]
        
        return result
        
    finally:
        if temp_filepath and os.path.exists(temp_filepath):
            os.unlink(temp_filepath)



# This function remains the public entry point that handles the list of files
def extract_1099_int(pdf_files: List[Any]) -> List[Dict[str, Any]]:
    """
    Public function responsible for iterating over the list of uploaded 1099-INT files
    and returning a combined list of extracted data.
    """
    if not pdf_files:
        return []
    
    all_extracted_data = []
    
    for file in pdf_files:
        try:
            # Use the internal function for processing
            data = _process_single_1099_int(file)
            all_extracted_data.append(data)
        except Exception as e:
            # Catch errors for individual files and continue processing
            all_extracted_data.append({
                "source_file": file.name, 
                "error": f"Failed to extract data: {e}"
            })

    return all_extracted_data