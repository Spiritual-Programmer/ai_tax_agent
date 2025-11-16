from ast import main
import pymupdf4llm
import re
from typing import Any, Dict, Optional
from .w2_patterns import * 


def extract_regex_group(text: str, pattern: str) -> Optional[str]:
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else None

def clean_and_convert_to_float(amount_str: str) -> Optional[float]:
    if not amount_str:
        return None
    
    cleaned = amount_str.replace(',', '').replace('$', '').strip()
    
    try:
        return float(cleaned)
    except ValueError:
        return None

def _get_box_value(markdown: str, pattern: str, key: str, data: Dict) -> None:
    """Helper to extract, clean, and store a single currency box value."""
    value_str = extract_regex_group(markdown, pattern)
    if value_str:
        data[key] = clean_and_convert_to_float(value_str)

def _extract_employee_name(markdown: str) -> Dict[str, str]:
    """Handles the complex primary/fallback logic for name extraction."""
    # Primary Search (Requires two capturing groups)
    # Note: DOTALL flag is needed here since re.search is called directly
    name_match = re.search(NAME_PRIMARY_PATTERN, markdown, re.DOTALL)
    
    if name_match:
        first_name = name_match.group(1)
        last_name = name_match.group(2)
    else:
        # Fallback Search (using two separate extract_regex_group calls)
        first_name = extract_regex_group(markdown, NAME_FALLBACK_FIRST_PATTERN)
        last_name = extract_regex_group(markdown, NAME_FALLBACK_LAST_PATTERN)
    
    if first_name and last_name:
        return {
            'first_name': first_name,
            'last_name': last_name,
            'full_name': f"{first_name} {last_name}"
        }
    return {}

def extract_employee_data(markdown: str) -> Dict[str, Any]:
    """Extracts all employee-specific fields (SSN, Address, Name)."""
    data: Dict[str, Any] = {}
    
    # SSN
    ssn = extract_regex_group(markdown, SSN_PATTERN)
    if ssn:
        data['ssn'] = ssn.replace(' ', '')
        
    # Address
    address = extract_regex_group(markdown, ADDRESS_PATTERN)
    if address:
        data['address'] = address
        
    # Name (Handled by complex helper)
    data.update(_extract_employee_name(markdown))
    return {'employee': data}


def extract_employer_data(markdown: str) -> Dict[str, Any]:
    """Extracts all employer-specific fields (EIN, Name, Address, Control No.)."""
    data: Dict[str, Any] = {}
    
    # EIN
    ein = extract_regex_group(markdown, EIN_PATTERN)
    if ein:
        data['ein'] = ein.replace(' ', '')
        
    # Employer Name and Address
    employer_info = extract_regex_group(markdown, EMPLOYER_INFO_PATTERN)
    if employer_info:
        parts = [p.strip() for p in employer_info.split(',')]
        if parts:
            data['name'] = parts[0]
            if len(parts) > 1:
                data['address'] = ', '.join(parts[1:])
                
    # Control Number
    control_num = extract_regex_group(markdown, CONTROL_NUM_PATTERN)
    if control_num:
        data['control_number'] = control_num

    return {'employer': data}


def extract_wages_and_taxes(markdown: str) -> Dict[str, Any]:
    """Extracts all standard federal wages and taxes (Boxes 1-7)."""
    data: Dict[str, Any] = {}
    
    _get_box_value(markdown, BOX_1_WAGES, 'box_1_wages', data)
    _get_box_value(markdown, BOX_2_FED_TAX, 'box_2_federal_tax_withheld', data)
    _get_box_value(markdown, BOX_3_SS_WAGES, 'box_3_ss_wages', data)
    _get_box_value(markdown, BOX_4_SS_TAX, 'box_4_ss_tax_withheld', data)
    _get_box_value(markdown, BOX_5_MEDICARE_WAGES, 'box_5_medicare_wages', data)
    _get_box_value(markdown, BOX_6_MEDICARE_TAX, 'box_6_medicare_tax_withheld', data)
    _get_box_value(markdown, BOX_7_SS_TIPS, 'box_7_ss_tips', data)
    
    return {'wages_and_taxes': data}


def extract_additional_info(markdown: str) -> Dict[str, Any]:
    """Extracts information from Boxes 12, 14, and State data (15-17)."""
    data: Dict[str, Any] = {}
    
    # Box 12a Code D
    _get_box_value(markdown, BOX_12A_CODE_D, 'box_12a_code_d_401k', data)
    
    # Box 14: Other
    other = extract_regex_group(markdown, BOX_14_OTHER)
    if other:
        data['box_14_other'] = other
    
    # Box 15: State
    state = extract_regex_group(markdown, BOX_15_STATE)
    if state:
        data['box_15_state'] = state
    
    # State Wages and Tax
    _get_box_value(markdown, BOX_16_STATE_WAGES, 'box_16_state_wages', data)
    _get_box_value(markdown, BOX_17_STATE_TAX, 'box_17_state_tax', data)
    
    return {'additional_info': data}


# --- Main Orchestrator Function (Former main_parser.py) ---

def parse_w2(pdf_file: str, debug: bool = False) -> Dict[str, Any]:
    markdown = pymupdf4llm.to_markdown(pdf_file)
    
    if debug:
        print("\n" + "="*60)
        print("RAW MARKDOWN OUTPUT:")
        print("="*60)
        print(markdown)
        print("="*60 + "\n")
    
    w2_data: Dict[str, Any] = {}
    
    w2_data.update(extract_employee_data(markdown))
    w2_data.update(extract_employer_data(markdown))
    w2_data.update(extract_wages_and_taxes(markdown))
    w2_data.update(extract_additional_info(markdown))

    # 3. FINAL STRUCTURE (Ensures top-level keys exist for consistency)
    final_w2: Dict[str, Any] = {
        'employee': w2_data.get('employee', {}),
        'employer': w2_data.get('employer', {}),
        'wages_and_taxes': w2_data.get('wages_and_taxes', {}),
        'additional_info': w2_data.get('additional_info', {})
    }
    
    return final_w2

text = parse_w2("./backend/w2.pdf")

print(text)
    