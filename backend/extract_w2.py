# parsers/parse_w2.py
from typing import List, Dict, Any
import pymupdf4llm
import re
import fitz  # PyMuPDF
from .w2_patterns import *  # keep all your regex patterns unchanged
import tempfile
import os

def extract_regex_group(text: str, pattern: str) -> str:
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else None

def clean_and_convert_to_float(amount_str: str) -> float:
    if not amount_str:
        return 0.0
    cleaned = amount_str.replace(',', '').replace('$', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def _get_box_value(markdown: str, pattern: str, key: str, data: Dict) -> None:
    value_str = extract_regex_group(markdown, pattern)
    if value_str:
        data[key] = clean_and_convert_to_float(value_str)

def _extract_employee_name(markdown: str) -> Dict[str, str]:
    name_match = re.search(NAME_PRIMARY_PATTERN, markdown, re.DOTALL)
    if name_match:
        first_name = name_match.group(1)
        last_name = name_match.group(2)
    else:
        first_name = extract_regex_group(markdown, NAME_FALLBACK_FIRST_PATTERN)
        last_name = extract_regex_group(markdown, NAME_FALLBACK_LAST_PATTERN)
    if first_name and last_name:
        return {'first_name': first_name, 'last_name': last_name, 'full_name': f"{first_name} {last_name}"}
    return {}

def extract_employee_data(markdown: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    ssn = extract_regex_group(markdown, SSN_PATTERN)
    if ssn:
        data['ssn'] = ssn.replace(' ', '')
    address = extract_regex_group(markdown, ADDRESS_PATTERN)
    if address:
        data['address'] = address
    data.update(_extract_employee_name(markdown))
    return {'employee': data}

def extract_employer_data(markdown: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    ein = extract_regex_group(markdown, EIN_PATTERN)
    if ein:
        data['ein'] = ein.replace(' ', '')
    employer_info = extract_regex_group(markdown, EMPLOYER_INFO_PATTERN)
    if employer_info:
        parts = [p.strip() for p in employer_info.split(',')]
        if parts:
            data['name'] = parts[0]
            if len(parts) > 1:
                data['address'] = ', '.join(parts[1:])
    control_num = extract_regex_group(markdown, CONTROL_NUM_PATTERN)
    if control_num:
        data['control_number'] = control_num
    return {'employer': data}

def extract_wages_and_taxes(markdown: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    _get_box_value(markdown, BOX_1_WAGES, 'wages', data)
    _get_box_value(markdown, BOX_2_FED_TAX, 'federal_tax_withheld', data)
    _get_box_value(markdown, BOX_3_SS_WAGES, 'ss_wages', data)
    _get_box_value(markdown, BOX_4_SS_TAX, 'ss_tax_withheld', data)
    _get_box_value(markdown, BOX_5_MEDICARE_WAGES, 'medicare_wages', data)
    _get_box_value(markdown, BOX_6_MEDICARE_TAX, 'medicare_tax_withheld', data)
    _get_box_value(markdown, BOX_7_SS_TIPS, 'ss_tips', data)
    return {'wages_and_taxes': data}

def extract_additional_info(markdown: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    _get_box_value(markdown, BOX_12A_CODE_D, 'box_12a_401k', data)
    other = extract_regex_group(markdown, BOX_14_OTHER)
    if other:
        data['box_14_other'] = other
    state = extract_regex_group(markdown, BOX_15_STATE)
    if state:
        data['state'] = state
    _get_box_value(markdown, BOX_16_STATE_WAGES, 'state_wages', data)
    _get_box_value(markdown, BOX_17_STATE_TAX, 'state_tax_withheld', data)
    return {'additional_info': data}

def parse_w2(pdf_file: Any) -> Dict[str, Any]:
    """Parse a single W2 PDF into standardized dictionary for tax_return."""
    temp_filepath = None
    try:
        pdf_bytes = pdf_file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_bytes)
            temp_filepath = tmp.name
        markdown = pymupdf4llm.to_markdown(temp_filepath)
    finally:
        if temp_filepath and os.path.exists(temp_filepath):
            os.unlink(temp_filepath)

    w2_data: Dict[str, Any] = {}
    w2_data.update(extract_employee_data(markdown))
    w2_data.update(extract_employer_data(markdown))
    w2_data.update(extract_wages_and_taxes(markdown))
    w2_data.update(extract_additional_info(markdown))

    # Flatten for tax_return compatibility
    final_w2 = {
        'source_file': getattr(pdf_file, 'name', None),
        'first_name': w2_data['employee'].get('first_name'),
        'last_name': w2_data['employee'].get('last_name'),
        'ssn': w2_data['employee'].get('ssn'),
        'filing_status': None,  # Not on W2
        'address': w2_data['employee'].get('address'),
        'employer_name': w2_data['employer'].get('name'),
        'employer_ein': w2_data['employer'].get('ein'),
        'wages': w2_data['wages_and_taxes'].get('wages', 0.0),
        'federal_tax_withheld': w2_data['wages_and_taxes'].get('federal_tax_withheld', 0.0),
        'state_tax_withheld': w2_data['additional_info'].get('state_tax_withheld', 0.0)
    }

    return final_w2

def extract_all_w2(pdf_files: List[Any]) -> List[Dict[str, Any]]:
    all_extracted_data = []
    for file in pdf_files:
        try:
            data = parse_w2(file)
            all_extracted_data.append(data)
        except Exception as e:
            all_extracted_data.append({
                "source_file": getattr(file, 'name', None),
                "error": f"Failed to extract data: {e}"
            })
    return all_extracted_data
