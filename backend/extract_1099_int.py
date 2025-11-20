from typing import List, Dict, Any
import io 
import tempfile # For creating temporary files
import os 
import pymupdf4llm
import re
from .w2_patterns import * 

def _process_single_1099_int(pdf_file) -> dict:
    """
    Internal function to extract data from a single Form 1099-INT PDF file.
    Writes the contents to a temporary file before processing to resolve the
    'bad filename' error from pymupdf4llm.
    """
    if pdf_file is None:
        return {}
        
    # 1. Read the file content into raw bytes
    pdf_bytes = pdf_file.read()
    temp_filepath = None
    
    try:
        # 2. Create a temporary file and write the bytes to it
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(pdf_bytes)
            # Store the path
            temp_filepath = tmp_file.name
        
        # 3. CRITICAL FIX: Pass the string path to pymupdf4llm.to_markdown
        text = pymupdf4llm.to_markdown(temp_filepath)
        
        result = {
            "source_file": pdf_file.name 
        }
        
        # --- Extraction Logic ---
        
        # Payer Name: Line after year
        payer = re.search(r'202[3-5]\n(.+?)(?=\n\d)', text, re.DOTALL)
        if payer:
            lines = payer.group(1).strip().split('\n')
            result["payer_name"] = lines[0] if lines else None
        
        # TINs: Adjacent EIN and SSN
        tins = re.search(r'(\d{2}-\d{7})(\d{3}-\d{2}-\d{4})', text)
        if tins:
            result["payer_tin"] = tins.group(1)
            result["recipient_tin"] = tins.group(2)
        
        # Recipient name: Line after SSN
        recip = re.search(r'\d{3}-\d{2}-\d{4}\n([A-Z][a-z]+ [A-Z][a-z]+)', text)
        if recip:
            result["recipient_name"] = recip.group(1)
        
        # Interest income: First non-zero decimal > $1
        amounts = re.findall(r'(\d+\.\d{2})', text)
        non_zero = [float(a) for a in amounts if float(a) > 1.0]
        if non_zero:
            result["box1_interest_income"] = non_zero[0]
        
        # State tax: Usually last small amount
        small_amounts = [float(a) for a in amounts if 0 < float(a) <= 10]
        if small_amounts:
            result["box17_state_tax_withheld"] = small_amounts[-1]
        
        return result
        
    finally:
        # 4. Clean up the temporary file if it was created
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