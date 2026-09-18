# Land Record Digitization & Verification System (BhumiSetu)

A full-stack, production-ready Flask web platform for digitizing, verifying, and managing cadastral land records, registered sale deeds, patta allotment certificates, and revenue registry entries.

## ?? Key Features

1. **Optical Character Recognition (OCR) Engine**:
   - Supports scanned deeds (PDF, PNG, JPG, JPEG, TIFF, TXT).
   - Automatically parses deed numbers, Khasra numbers, survey numbers, purchaser/owner names, co-owners, village, tehsil, district, area, valuation, registration date, and boundary coordinates.
   - 1-click **"Digitize into Land Record"** auto-mapping workflow.

2. **Automated Cadastral Duplicate & Overlap Detector**:
   - Compares incoming and existing parcels by Khasra number, survey number, village, district, owner name similarity, and area thresholds.
   - Calculates collision scores (0% - 100%) and flags records into `High`, `Medium`, and `Low` risk.
   - Global registry scan utility.

3. **Side-by-Side Record & Deed Comparator**:
   - Visual diff comparison between official registry entries and physical deed OCR extracts.
   - Highlights spelling variations, area discrepancies (acres/sqft), and valuation mismatches in green, yellow, and red.

4. **Multi-Role Access Control & Workflow**:
   - **Administrator**: User provisioning, global registry audits, duplicate resolutions.
   - **Revenue Officer**: Upload deeds, execute OCR, digitize land parcels, edit records.
   - **Verification Officer**: Review pending queue, inspect 30-year title chain, check cadastral boundaries, approve or reject records.

5. **Compliance Audit Trail**:
   - Immutable log capturing every login, record creation, OCR scan, duplicate check, and verification approval.

6. **Analytics & Reports**:
   - Dynamic charts by district and land use classification.
   - Full CSV export of records and audit trails.

---

## ?? Demo Accounts

| Role | Email Login | Password | Capabilities |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@example.com` | `Demo@123` | Full admin rights, user management, global scan |
| **Revenue Officer** | `revenue@example.com` | `Demo@123` | Upload physical deeds, run OCR, digitize records |
| **Verification Officer** | `verify@example.com` | `Demo@123` | Review pending queue, approve/reject parcels |

---

## ??? Installation & Setup

### 1. Navigate to Project Directory
```powershell
cd land_record_digitization
```

### 2. Create and Activate Virtual Environment (Optional)
```powershell
python -m venv venv
# Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Run the Web Application
```powershell
python app.py
```

### 5. Open in Web Browser
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## ?? Project Structure

```
land_record_digitization/
+-- app.py                     # Main application factory & auto-seeder
+-- config.py                  # Environment & SQLite database config
+-- requirements.txt           # Pinned dependencies
+-- README.md                  # Documentation
+-- database.db                # Auto-initialized SQLite database
¦
+-- models/                    # SQLAlchemy database models
¦   +-- __init__.py
¦   +-- user.py                # User auth & roles
¦   +-- land_record.py         # Cadastral land parcel registry
¦   +-- document.py            # Uploaded deeds & OCR metadata
¦   +-- verification.py        # Officer approval decisions
¦   +-- audit_log.py           # Immutable audit trails
¦
+-- routes/                    # Modular Flask blueprints
¦   +-- __init__.py
¦   +-- auth.py                # Sign in, sign out, profiles
¦   +-- dashboard.py           # KPI metrics & analytics
¦   +-- records.py             # CRUD records & duplicate checks
¦   +-- documents.py           # Upload deeds & trigger OCR
¦   +-- verification.py        # Verification officer review queue
¦   +-- reports.py             # Export CSV & district summaries
¦   +-- admin.py               # Officer management & system health
¦
+-- services/                  # Smart core engines
¦   +-- ocr_service.py         # Deed OCR parser & image generator
¦   +-- duplicate_detector.py  # Spatial & Khasra overlap detection
¦   +-- record_comparator.py   # Registry vs Deed diff comparator
¦
+-- templates/                 # Jinja2 HTML templates
¦   +-- base.html
¦   +-- index.html
¦   +-- login.html
¦   +-- dashboard.html
¦   +-- upload.html
¦   +-- ocr_result.html
¦   +-- records.html
¦   +-- record_details.html
¦   +-- record_form.html
¦   +-- verification.html
¦   +-- duplicates.html
¦   +-- mismatches.html
¦   +-- reports.html
¦   +-- admin.html
¦   +-- error.html
¦
+-- static/                    # Frontend styling & interactions
¦   +-- css/style.css          # Custom responsive CSS
¦   +-- js/script.js           # Dynamic alert dismiss & helpers
¦   +-- images/
¦
+-- uploads/                   # Uploaded deed images & PDFs
+-- reports/                   # Exported CSV reports
```
