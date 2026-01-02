# AI Tax Agent

AI Tax Agent is a Python-based project that allows a user to upload multiple tax documents (W-2s, 1099-INTs, and 1099-SECs) and generates a completed Form 1040 based on the provided information.

The goal of this project is to automate the repetitive and error-prone process of manually transferring data from tax forms into a 1040.

---

## What It Does

- Accepts multiple tax documents:
  - W-2
  - 1099-INT
  - 1099-SEC
- Extracts relevant tax information from each document
- Aggregates the data across all uploaded forms
- Outputs a completed Form 1040

---

## Tech Stack

- Python
- PDF parsing libraries for document extraction
- Basic automation logic for data aggregation and form generation

---

## How It Works (High Level)

1. User uploads one or more tax documents (W-2s, 1099s)
2. The program extracts the required fields from each document
3. Data is combined and mapped to the appropriate fields on Form 1040
4. A completed 1040 is generated as output

---

## Project Status

This project is currently focused on core functionality:
- Accurate extraction
- Correct aggregation
- Valid 1040 output

Future improvements may include additional tax forms, validation, and a user interface.

---

## Disclaimer

This project is for educational and experimental purposes only and is not intended to replace professional tax advice.
