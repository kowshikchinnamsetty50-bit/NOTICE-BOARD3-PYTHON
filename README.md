# 🏛️ CampusPulse — College Notice Board Organizer

A clean, modern, and beginner-friendly Python web application built with **Streamlit** to help college students, faculty, and administrative staff manage, publish, search, import, and track campus notices seamlessly.

---

## 🌟 Key Features

1. **📊 Interactive Analytics Dashboard**
   - **Live Metric Cards:** Total notices, active notices, upcoming notices, and expired notices.
   - **🚨 Critical Action Alerts & Approaching Deadlines:** Instant banner alerts for urgent notices and announcements closing within 24–72 hours.
   - **Interactive Charts:** Category distribution and status breakdown visual charts powered by Altair.
   - **📈 Monthly Activity Timeline:** Tracks notice publication volumes month-by-month.

2. **🤖 Smart Automatic Status & Expiry Detection**
   - Automatically determines whether a notice is **Active**, **Upcoming**, or **Expired** by evaluating dates against the current date:
     - 🟢 **Active:** `Published Date <= Today <= Expiry Date` (currently ongoing/actionable).
     - 🔵 **Upcoming:** `Published Date > Today` (scheduled for future release; automatically activates when date arrives).
     - ⚪ **Expired:** `Expiry Date < Today` (past deadline, preserved for historical records).
   - Dynamically calculates human-readable relative timelines (e.g., *"Expires in 3 days"*, *"Starts in 5 days"*, *"Expired 2 days ago"*) and highlights urgent deadline warnings.

3. **🎯 4-Tier Priority System**
   - **Critical (🚨):** High-urgency notifications (e.g. fee deadlines, exam admit cards, weather advisories) with glowing badge accents.
   - **High (🔴):** Major academic and placement notices.
   - **Medium (🟡):** Standard student events, meetings, and club activities.
   - **Low (🔵):** General circulars and sports updates.

4. **📋 Comprehensive Search & Multi-Facet Filtering**
   - **Multi-field Search:** Search across notice title, description, category, department, audience, and ID.
   - **Facet Filters:** Category, status, priority, and audience.
   - **Sorting Modes:** Sort by published date (newest/oldest), expiry date (soonest/latest), priority (critical to low), and title (A-Z / Z-A).
   - **View Toggle:** Switch between a card layout and an interactive tabular data view.

5. **🛡️ Duplicate Prevention & Input Validation**
   - **Duplicate Detection:** Prevents creating identical notices in the same category using normalized title matching.
   - **Strict Input Validation:** Enforces title length (3–120 chars), description length (10–5000 chars), valid calendar dates (year range 2000–2040), and guarantees expiry dates cannot precede publication dates.

6. **📥 Bulk CSV Import with Error Reporting**
   - Upload multiple notices simultaneously from any CSV file.
   - Downloadable sample CSV template (`notices_import_template.csv`).
   - Granular row-by-row validation with explicit error logging detailing exact row numbers and rejection causes.

7. **✏️ Notice Management (Edit & Delete)**
   - Pre-populated edit forms to update any details, dates, or priority levels of published notices.
   - Safe deletion flow with mandatory confirmation to prevent accidental data loss.

8. **📑 Reports & One-Click Export**
   - Category-wise analytics matrix and department activity tables.
   - **Export to CSV:** Download all notices as `.csv` for Excel or spreadsheet analysis.
   - **Export to JSON:** Download full structured JSON archive for backups or API integration.

9. **🔒 Safety Backups & Audit Logging**
   - **Automatic Backup:** Every modification creates a safety backup at `data/notices.json.bak`.
   - **Atomic Writes:** File saves use temporary file replacement to prevent file corruption.
   - **Timestamped Activity Logs:** Operations are logged with timestamps in `data/app.log` and viewable inside the UI.

10. **📦 Preloaded Realistic Sample Data**
    - Includes **32 realistic college notices** covering Academics, Examinations, Placements, Cultural Fests, Sports, Scholarships, Hostels, and Administration.
    - Dynamically anchored around the current date, guaranteeing a balanced distribution of Active, Expired, and Upcoming notices whenever the app is launched.

---

## 📂 Project Structure

```text
c:/Users/Mohith/Desktop/python 1/
├── app.py                     # Main Streamlit application entry point
├── config.py                  # System configuration, constants, categories, and colors
├── requirements.txt           # Project dependencies
├── README.md                  # Complete documentation and user guide
├── run.bat                    # One-click Windows batch launcher
├── run.ps1                    # One-click Windows PowerShell launcher
├── .streamlit/
│   └── config.toml            # Streamlit theme and server configuration
├── data/
│   ├── notices.json           # Primary local database (JSON format)
│   ├── notices.csv            # Auto-synchronized CSV copy for external tools
│   ├── notices.json.bak       # Automatic safety backup
│   └── app.log                # Timestamped application audit log
├── modules/
│   ├── __init__.py            # Python package initialization
│   ├── data_manager.py        # Storage handling, CRUD operations, validation & auto-status logic
│   └── ui_components.py       # Custom CSS styling, badges, metric cards & chart helpers
└── tests/
    └── test_data_manager.py   # Automated 15-point unit test suite
```

---

## 🛠️ Technology Stack

- **Python 3.10+ / 3.14**
- **Streamlit** (Web Application Framework)
- **Pandas** (Data analysis, tabular viewing, and CSV processing)
- **Altair** (Declarative statistical data visualization)
- **JSON & CSV** (Lightweight, zero-configuration local persistence)

---

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
streamlit run app.py
```

*Alternative (if `streamlit` is not directly on your system PATH):*
```bash
python -m streamlit run app.py
```
*Or on Windows, simply double-click [run.bat](file:///c:/Users/Mohith/Desktop/python%201/run.bat) or run `./run.ps1` in PowerShell.*

### 3. Run Automated Tests
```bash
python tests/test_data_manager.py
```

---

## 🧭 Application Pages

| Page | Description |
| :--- | :--- |
| **📊 Dashboard** | High-level metrics, expiration alerts, visual category/status charts, monthly activity trends, and urgent notices. |
| **📋 Browse & Search** | Search through all notices, apply multi-filters, and switch between Card and Table modes. |
| **➕ Add New Notice** | Publish new announcements with real-time input validation, duplicate check, and live card preview. |
| **📥 Bulk CSV Import** | Batch upload notices with row-by-row error validation and downloadable template. |
| **✏️ Edit & Manage** | Select any notice to update its content or safely delete it with confirmation. |
| **📑 Reports & Analytics** | View summary matrices, monthly publication trends, and download notice archives as CSV or JSON files. |
| **ℹ️ User Guide & Logs** | Detailed explanation of date rules, data schemas, live activity logs viewer, and a demo reset button. |

---

## 📄 License
This project is open-source and free to use for educational, college campus, and personal projects.
