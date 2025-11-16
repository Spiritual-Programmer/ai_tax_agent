# --- Employee Information ---
SSN_PATTERN = r'Employee.*?social\s*security\s*number.*?(\d{3}\s*-\s*\d{2}\s*-\s*\d{4})'
ADDRESS_PATTERN = r'Employee.*?address.*?\*\*([^*]+)\*\*[\s\S]*?Employer\s*identification\s*number'
# Name: Primary match requires two capturing groups for first/last name near an address
NAME_PRIMARY_PATTERN = r'\*\*([A-Z][a-z]+)\*\*[^*]*\*\*([A-Z][a-z]+)\*\*[^*]*\*\*\d+\s+\w+\s+St'
# Name: Fallback patterns for searching after the address/ZIP label
NAME_FALLBACK_FIRST_PATTERN = r'Employee.*?address.*?ZIP.*?\*\*([A-Z][a-z]+)\*\*'
NAME_FALLBACK_LAST_PATTERN = r'Employee.*?address.*?ZIP.*?\*\*[A-Z][a-z]+\*\*[^*]*\*\*([A-Z][a-z]+)\*\*'

# --- Employer Information ---
EIN_PATTERN = r'Employer\s*identification\s*number.*?(\d{2}\s*-\s*\d{7})'
EMPLOYER_INFO_PATTERN = r'Employer.*?name,\s*address.*?\*\*([^*]+)\*\*'
CONTROL_NUM_PATTERN = r'Control\s*number.*?\*\*([^*]+)\*\*'

# --- Wages and Taxes (Standardized Box Patterns) ---
BOX_1_WAGES = r'\*\*1\*\*.*?Wages.*?compensation.*?\*\*([0-9,\.]+)\*\*'
BOX_2_FED_TAX = r'\*\*2\*\*.*?Federal\s*income\s*tax\s*withheld.*?\*\*([0-9,\.]+)\*\*'
BOX_3_SS_WAGES = r'\*\*3\*\*.*?Social\s*security\s*wages.*?\*\*([0-9,\.]+)\*\*'
BOX_4_SS_TAX = r'\*\*4\*\*.*?Social\s*security\s*tax\s*withheld.*?\*\*([0-9,\.]+)\*\*'
BOX_5_MEDICARE_WAGES = r'\*\*5\*\*.*?Medicare\s*wages.*?\*\*([0-9,\.]+)\*\*'
BOX_6_MEDICARE_TAX = r'\*\*6\*\*.*?Medicare\s*tax\s*withheld.*?\*\*([0-9,\.]+)\*\*'
BOX_7_SS_TIPS = r'\*\*7\*\*.*?Social\s*security\s*tips.*?\*\*([0-9,\.]+)\*\*'

# --- Additional Information ---
BOX_12A_CODE_D = r'\*\*12a\*\*.*?D:.*?\*\*([0-9,\.]+)'
BOX_14_OTHER = r'\*\*14\*\*.*?Other.*?\*\*([^*]+)\*\*'
BOX_15_STATE = r'\*\*15\*\*.*?State.*?\*\*([A-Z]{2})\*\*'
BOX_16_STATE_WAGES = r'\*\*16\*\*.*?State\s*wages.*?\*\*([0-9,\.]+)\*\*'
BOX_17_STATE_TAX = r'\*\*17\*\*.*?State\s*income\s*tax.*?\*\*([0-9,\.]+)\*\*'