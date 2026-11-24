"""
Data Manager Module for Notice Board Organizer.
Handles JSON/CSV storage, safe backup protection, dynamic status calculation,
input validation, duplicate prevention, CSV bulk import with error reporting,
timestamped application logging, and analytics.
"""

import csv
import io
import json
import logging
import os
import re
import shutil
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd

from config import (
    APP_LOG_FILE,
    AUDIENCES,
    CATEGORIES,
    DATA_DIR,
    NOTICES_BACKUP_FILE,
    NOTICES_CSV_FILE,
    NOTICES_JSON_FILE,
    PRIORITIES,
    STATUS_ACTIVE,
    STATUS_EXPIRED,
    STATUS_UPCOMING,
)


def ensure_data_directory() -> None:
    """Ensure the data directory exists."""
    os.makedirs(DATA_DIR, exist_ok=True)


def get_application_logger() -> logging.Logger:
    """Configure and retrieve timestamped application logger."""
    ensure_data_directory()
    app_logger = logging.getLogger("NoticeBoardOrganizer")
    if not app_logger.handlers:
        app_logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(APP_LOG_FILE, encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        app_logger.addHandler(file_handler)
    return app_logger


logger = get_application_logger()


def normalize_title(text: str) -> str:
    """Normalize title for fuzzy duplicate detection (lowercase, alphanumeric only)."""
    if not text:
        return ""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def compute_notice_status(
    published_date: Any, expiry_date: Any, reference_date: Optional[date] = None
) -> Tuple[str, int, str, Optional[str]]:
    """
    Automatically compute notice status (Active, Upcoming, Expired)
    based on published date and expiry date compared to reference date (today).

    Returns:
        tuple: (status, days_count, relative_time_label, deadline_warning)
    """
    if reference_date is None:
        reference_date = date.today()

    # Convert strings to date if necessary
    if isinstance(published_date, str):
        published_date = datetime.strptime(published_date.strip()[:10], "%Y-%m-%d").date()
    elif isinstance(published_date, datetime):
        published_date = published_date.date()

    if isinstance(expiry_date, str):
        expiry_date = datetime.strptime(expiry_date.strip()[:10], "%Y-%m-%d").date()
    elif isinstance(expiry_date, datetime):
        expiry_date = expiry_date.date()

    if published_date > reference_date:
        days = (published_date - reference_date).days
        warning = "🗓️ Goes Live Tomorrow" if days == 1 else None
        return (
            STATUS_UPCOMING,
            days,
            f"Starts in {days} day{'s' if days != 1 else ''}",
            warning,
        )
    elif expiry_date < reference_date:
        days = (reference_date - expiry_date).days
        return (
            STATUS_EXPIRED,
            days,
            f"Expired {days} day{'s' if days != 1 else ''} ago",
            None,
        )
    else:
        days = (expiry_date - reference_date).days
        if days == 0:
            return STATUS_ACTIVE, 0, "Expires today!", "⚠️ Closes Today!"
        elif days == 1:
            return STATUS_ACTIVE, 1, "Expires tomorrow", "⏳ Closes Tomorrow (24 hrs left)!"
        elif days <= 3:
            return STATUS_ACTIVE, days, f"Expires in {days} days", f"⚡ Closes in {days} days"
        return STATUS_ACTIVE, days, f"Expires in {days} day{'s' if days != 1 else ''}", None


def check_duplicate_notice(
    title: str,
    category: str,
    existing_notices: List[Dict[str, Any]],
    exclude_id: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Check if a notice with an identical normalized title exists in the same category.
    Returns:
        (is_duplicate, existing_notice_id)
    """
    norm_new = normalize_title(title)
    if not norm_new:
        return False, None

    for n in existing_notices:
        if exclude_id and n.get("id") == exclude_id:
            continue
        if n.get("category") == category and normalize_title(n.get("title", "")) == norm_new:
            return True, n.get("id")

    return False, None


def validate_notice_input(
    title: str,
    description: str,
    category: str,
    published_date: Any,
    expiry_date: Any,
    priority: str = "Medium",
    audience: str = "All Students",
    department: str = "",
    existing_notices: Optional[List[Dict[str, Any]]] = None,
    exclude_id: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Validates notice input fields to prevent empty data, invalid dates, and duplicates.

    Returns:
        (is_valid, error_message)
    """
    if not title or not title.strip():
        return False, "Notice title cannot be empty."

    clean_title = title.strip()
    if len(clean_title) < 3:
        return False, "Title must be at least 3 characters long."
    if len(clean_title) > 120:
        return False, "Title cannot exceed 120 characters."

    if not description or not description.strip():
        return False, "Notice description cannot be empty."

    clean_desc = description.strip()
    if len(clean_desc) < 10:
        return False, "Description must be at least 10 characters long to provide sufficient detail."
    if len(clean_desc) > 5000:
        return False, "Description exceeds the 5,000 character maximum limit."

    if category not in CATEGORIES:
        return False, f"Category '{category}' is invalid. Please select from the standard categories."

    if priority not in PRIORITIES:
        return False, f"Priority '{priority}' is invalid. Allowed: {', '.join(PRIORITIES)}"

    if audience not in AUDIENCES:
        return False, f"Audience '{audience}' is invalid. Allowed: {', '.join(AUDIENCES)}"

    # Parse and validate dates
    if isinstance(published_date, str):
        try:
            published_date = datetime.strptime(published_date.strip()[:10], "%Y-%m-%d").date()
        except ValueError:
            return False, "Published date must be in YYYY-MM-DD format."
    elif isinstance(published_date, datetime):
        published_date = published_date.date()

    if isinstance(expiry_date, str):
        try:
            expiry_date = datetime.strptime(expiry_date.strip()[:10], "%Y-%m-%d").date()
        except ValueError:
            return False, "Expiry date must be in YYYY-MM-DD format."
    elif isinstance(expiry_date, datetime):
        expiry_date = expiry_date.date()

    if not isinstance(published_date, date) or not isinstance(expiry_date, date):
        return False, "Both published date and expiry date are required."

    # Year range guard (prevents year typos like 0026 or 22026)
    if published_date.year < 2000 or published_date.year > 2040:
        return False, f"Published date year {published_date.year} is outside valid range (2000-2040)."
    if expiry_date.year < 2000 or expiry_date.year > 2040:
        return False, f"Expiry date year {expiry_date.year} is outside valid range (2000-2040)."

    if expiry_date < published_date:
        return False, f"Expiry date ({expiry_date}) cannot be earlier than the Published date ({published_date})."

    # Duplicate check
    if existing_notices is not None:
        is_dup, dup_id = check_duplicate_notice(clean_title, category, existing_notices, exclude_id)
        if is_dup:
            return False, f"Duplicate notice detected: A notice with this title already exists in category '{category}' (ID: {dup_id})."

    return True, None


def generate_sample_notices(anchor_date: Optional[date] = None) -> List[Dict[str, Any]]:
    """
    Generates 32 realistic, detailed college notices dynamically anchored
    around the given reference date (defaults to today).
    Includes Critical, High, Medium, and Low priorities with Active, Expired, and Upcoming statuses.
    """
    if anchor_date is None:
        anchor_date = date.today()

    samples_blueprint = [
        # --- ACTIVE NOTICES (Ongoing deadlines, open registrations) ---
        {
            "title": "Autumn End-Semester Exam Schedule 2026 Released",
            "category": "Examinations",
            "description": "The detailed timetable for undergraduate and postgraduate end-semester examinations is now published. Students must download their admit cards from the student portal before the commencement of exams. Check room allocations and seating plans on department notice boards.",
            "pub_offset": -5,
            "exp_offset": 12,
            "priority": "Critical",
            "audience": "All Students",
            "department": "Controller of Examinations",
        },
        {
            "title": "Google & Microsoft Campus Placement Drive Registration",
            "category": "Placements & Internships",
            "description": "Registration is open for the upcoming campus recruitment drive for final year B.Tech, MCA, and M.Tech students. Eligible branches include CSE, IT, ECE, and AI/DS. Upload your updated resume on the placement portal and attend the mandatory pre-placement talk.",
            "pub_offset": -3,
            "exp_offset": 1,
            "priority": "Critical",
            "audience": "Final Year Students",
            "department": "Training & Placement Cell",
        },
        {
            "title": "National Hackathon 2026: Call for Team Registrations",
            "category": "Events & Cultural",
            "description": "Join the 36-hour National Hackathon organized by the Department of Computer Science. Exciting cash prizes worth $5,000, internship opportunities, and mentorship from top industry leaders. Teams of 2 to 4 students can register through the tech club portal.",
            "pub_offset": -8,
            "exp_offset": 10,
            "priority": "Medium",
            "audience": "All Students",
            "department": "Tech Innovation Club",
        },
        {
            "title": "Annual Merit & Need-Based Scholarship Applications Open",
            "category": "Scholarships & Aid",
            "description": "Applications are invited for the Dean's Merit Scholarship and Institutional Need-Based Financial Aid for the current academic session. Eligible students with a CGPA above 8.5 or household income criteria should submit supporting income certificates and transcripts.",
            "pub_offset": -10,
            "exp_offset": 14,
            "priority": "High",
            "audience": "Undergraduate (UG)",
            "department": "Financial Aid Office",
        },
        {
            "title": "Central Library Book Clearance & Overdue Waiver Week",
            "category": "Academics",
            "description": "Return all borrowed books with complete fine waiver during the annual Library Clearance Week. Students planning to apply for no-dues clearance for semester completion are strongly advised to clear all pending records.",
            "pub_offset": -4,
            "exp_offset": 2,
            "priority": "Medium",
            "audience": "All Students",
            "department": "Central Library",
        },
        {
            "title": "Inter-Department Basketball Championship Fixtures",
            "category": "Sports & Athletics",
            "description": "The annual Inter-Department Basketball Tournament begins this week at the Indoor Sports Arena. Come cheer for your department teams! Matches will be held daily from 4:30 PM to 8:00 PM. Referees and medical assistance will be on-site.",
            "pub_offset": -2,
            "exp_offset": 7,
            "priority": "Low",
            "audience": "All Students",
            "department": "Department of Physical Education",
        },
        {
            "title": "Hostel Mess Committee Monthly Feedback Meeting",
            "category": "Campus & Hostel",
            "description": "All hostel block representatives are invited to attend the monthly mess review meeting with the Chief Warden and catering supervisors in Conference Hall B. Discuss menu revisions, hygiene ratings, and feedback on food quality.",
            "pub_offset": -1,
            "exp_offset": 4,
            "priority": "Medium",
            "audience": "Hostellers & Residents",
            "department": "Hostel Management Committee",
        },
        {
            "title": "Elective Course Bidding for Upcoming Spring Term",
            "category": "Academics",
            "description": "The portal for open elective selection for the Spring semester is now active. Students in 4th and 6th semesters should choose their preferred open humanities, management, and interdisciplinary engineering courses before slots fill up.",
            "pub_offset": -6,
            "exp_offset": 5,
            "priority": "High",
            "audience": "Undergraduate (UG)",
            "department": "Academic Affairs",
        },
        {
            "title": "Workshop on Generative AI & Cloud Native Architecture",
            "category": "Academics",
            "description": "The IEEE Student Branch is hosting a hands-on technical workshop on Large Language Models, Retrieval Augmented Generation, and Container Orchestration on Saturday in Seminar Hall 1. Certificates will be provided to all attendees.",
            "pub_offset": -4,
            "exp_offset": 0,
            "priority": "High",
            "audience": "All Students",
            "department": "IEEE Student Chapter",
        },
        {
            "title": "Fee Payment Window for Upcoming Semester Installment",
            "category": "Administrative",
            "description": "Notice regarding payment of tuition and hostel fees for the upcoming semester. Students must pay via the official SBI Collect portal or college ERP. Late fee penalties will be applicable after the due date.",
            "pub_offset": -7,
            "exp_offset": 8,
            "priority": "Critical",
            "audience": "All Students",
            "department": "Finance & Accounts Office",
        },
        {
            "title": "Blood Donation Camp in Association with Red Cross",
            "category": "Events & Cultural",
            "description": "The National Service Scheme (NSS) unit is organizing a voluntary blood donation drive at the Student Activity Center. All healthy students and faculty are encouraged to donate and save lives. Refreshments and donor badges will be distributed.",
            "pub_offset": -3,
            "exp_offset": 1,
            "priority": "Medium",
            "audience": "All Students",
            "department": "NSS Volunteers Cell",
        },
        {
            "title": "Summer Internship Opportunity at DRDO & ISRO Centers",
            "category": "Placements & Internships",
            "description": "Applications are open for undergraduate research fellowships and summer internship projects at leading national laboratories. Pre-requisites include minimum CGPA of 8.0 and department recommendation letter.",
            "pub_offset": -2,
            "exp_offset": 15,
            "priority": "High",
            "audience": "Undergraduate (UG)",
            "department": "R&D Industry Liaison Cell",
        },

        # --- UPCOMING NOTICES (Scheduled future events, announcements) ---
        {
            "title": "Annual Cultural Festival 'AURA 2027' Auditions",
            "category": "Events & Cultural",
            "description": "Auditions for music bands, western dance, classical arts, dramatics, and fashion club for the upcoming annual cultural festival 'AURA 2027'. Registrations open next week on the cultural committee website.",
            "pub_offset": 5,
            "exp_offset": 25,
            "priority": "Medium",
            "audience": "All Students",
            "department": "Student Council",
        },
        {
            "title": "Winter Vacation & Hostel Closure Schedule Announcement",
            "category": "Campus & Hostel",
            "description": "College offices and hostels will observe winter recess starting next month. Students intending to stay back on campus for research projects or internship work must submit written dean approval.",
            "pub_offset": 1,
            "exp_offset": 30,
            "priority": "High",
            "audience": "Hostellers & Residents",
            "department": "Dean of Student Affairs",
        },
        {
            "title": "Inter-University Cricket Championship 2027 Trials",
            "category": "Sports & Athletics",
            "description": "Open selection trials for the college Men's and Women's cricket teams representing the university in the upcoming North Zone Inter-University Tournament. Bring your own cricket kit and identity card.",
            "pub_offset": 4,
            "exp_offset": 18,
            "priority": "Low",
            "audience": "All Students",
            "department": "Department of Physical Education",
        },
        {
            "title": "International Conference on Cyber Physical Systems (ICCPS)",
            "category": "Academics",
            "description": "Call for research papers and student posters for the 5th International Conference on Cyber Physical Systems. Selected peer-reviewed papers will be submitted for indexing in Scopus and IEEE Xplore.",
            "pub_offset": 7,
            "exp_offset": 45,
            "priority": "Medium",
            "audience": "Postgraduate (PG)",
            "department": "School of Computer Engineering",
        },
        {
            "title": "Campus Wi-Fi Infrastructure Upgrade Downtime Notice",
            "category": "Administrative",
            "description": "The Campus IT Centre will conduct a core router upgrade and high-speed fiber backbone maintenance. Wi-Fi networks in library and academic blocks will experience intermittent outages over the weekend.",
            "pub_offset": 2,
            "exp_offset": 5,
            "priority": "Medium",
            "audience": "All Students",
            "department": "IT Infrastructure Services",
        },
        {
            "title": "Alumni Mentorship Series: Careers in Product Management",
            "category": "Placements & Internships",
            "description": "Distinguished alumnus Mr. Ananya Roy (VP of Product, Stripe) will host an interactive session on transition strategies from software engineering into product leadership and tech entrepreneurship.",
            "pub_offset": 6,
            "exp_offset": 14,
            "priority": "Low",
            "audience": "Final Year Students",
            "department": "Alumni Relations Office",
        },
        {
            "title": "Semester Grade Card Distribution & Grievance Window",
            "category": "Examinations",
            "description": "Physical grade cards for the previous semester will be distributed by department coordinators. Any discrepancy in marks or grade recalculation queries must be filed within the scheduled redressal window.",
            "pub_offset": 8,
            "exp_offset": 22,
            "priority": "High",
            "audience": "Undergraduate (UG)",
            "department": "Controller of Examinations",
        },
        {
            "title": "E-Vehicle Campus Shuttle Service Rollout",
            "category": "Campus & Hostel",
            "description": "In line with our Green Campus initiative, a new fleet of solar-assisted electric shuttle buses will operate free of cost between the Main Gate, Academic Blocks, and Girls/Boys Hostels starting next month.",
            "pub_offset": 10,
            "exp_offset": 35,
            "priority": "Low",
            "audience": "All Students",
            "department": "Estate & Campus Services",
        },

        # --- EXPIRED NOTICES (Past events, closed deadlines, completed phases) ---
        {
            "title": "Mid-Term Examination Re-Evaluation Request Deadline",
            "category": "Examinations",
            "description": "The portal for requesting paper inspection and marks re-totaling for mid-semester tests is now officially closed. Evaluated answersheets have been deposited with the department records archive.",
            "pub_offset": -25,
            "exp_offset": -10,
            "priority": "Critical",
            "audience": "All Students",
            "department": "Controller of Examinations",
        },
        {
            "title": "Freshers Induction & Orientation Programme 2026",
            "category": "Events & Cultural",
            "description": "Welcome program for newly admitted first-year undergraduate students, including campus tour, faculty introduction, club showcases, and address by the Vice Chancellor in the University Auditorium.",
            "pub_offset": -40,
            "exp_offset": -30,
            "priority": "Medium",
            "audience": "Undergraduate (UG)",
            "department": "Orientation Taskforce",
        },
        {
            "title": "TCS CodeVita Season 13 Registration Closes",
            "category": "Placements & Internships",
            "description": "Final reminder to register for TCS CodeVita programming contest. Grand winners receive direct interview waivers for digital and prime developer profiles. Submissions closed on the portal.",
            "pub_offset": -30,
            "exp_offset": -12,
            "priority": "High",
            "audience": "Final Year Students",
            "department": "Training & Placement Cell",
        },
        {
            "title": "Diwali Festival Break & Campus Holiday Circular",
            "category": "Administrative",
            "description": "The Institute will remain closed on account of Diwali festivities. All regular academic classes, laboratories, and administrative offices remained suspended during this official break period.",
            "pub_offset": -28,
            "exp_offset": -18,
            "priority": "High",
            "audience": "All Students",
            "department": "Registrar Office",
        },
        {
            "title": "Campus Cleanliness & Swachhata Drive 2026",
            "category": "Campus & Hostel",
            "description": "Special cleanliness drive undertaken across campus lawns, botanical gardens, and sports complexes. Volunteers from all departments participated enthusiastically and certificates were handed out.",
            "pub_offset": -35,
            "exp_offset": -22,
            "priority": "Low",
            "audience": "All Students",
            "department": "NSS Volunteers Cell",
        },
        {
            "title": "GATE & CAT Examination Free Coaching Registration",
            "category": "Academics",
            "description": "Weekend preparatory classes for GATE 2027 and CAT 2027 organized by the department faculty for aspiring students. Registration slots have been fully booked for this cohort.",
            "pub_offset": -45,
            "exp_offset": -15,
            "priority": "Medium",
            "audience": "Final Year Students",
            "department": "Career Guidance Cell",
        },
        {
            "title": "Robotics Club 'Battle of Bots' Project Pitching",
            "category": "Events & Cultural",
            "description": "Submission of project proposals, circuit schematics, and mechanical design blueprints for the intramural robotics showdown. All accepted teams have commenced hardware fabrication.",
            "pub_offset": -32,
            "exp_offset": -8,
            "priority": "Low",
            "audience": "All Students",
            "department": "Robotics Society",
        },
        {
            "title": "National Sports Day 5K Marathon Run & Tug-of-War",
            "category": "Sports & Athletics",
            "description": "Celebration of National Sports Day with campus mini-marathon, obstacle races, and friendly faculty vs student tug-of-war. Medals were presented by the Dean of Sports.",
            "pub_offset": -50,
            "exp_offset": -35,
            "priority": "Low",
            "audience": "All Students",
            "department": "Department of Physical Education",
        },
        {
            "title": "Government State Minority Scholarship Portal Closure",
            "category": "Scholarships & Aid",
            "description": "Deadline for submitting physical documentation and bank passbook verification for the State Government Post-Matric Scholarship has lapsed. Verified applications have been forwarded to the Directorate.",
            "pub_offset": -40,
            "exp_offset": -14,
            "priority": "High",
            "audience": "All Students",
            "department": "Social Welfare Cell",
        },
        {
            "title": "Hostel Room Allotment for 2nd Year Lateral Entry Students",
            "category": "Campus & Hostel",
            "description": "Room keys distribution and bed allocation in Hostel Blocks C and D for lateral entry admissions. Students have completed physical verification and occupied designated rooms.",
            "pub_offset": -60,
            "exp_offset": -25,
            "priority": "Medium",
            "audience": "Hostellers & Residents",
            "department": "Chief Warden Office",
        },
        {
            "title": "Guest Lecture on Semiconductor Fabrication & Nanotechnology",
            "category": "Academics",
            "description": "Special technical lecture delivered by Dr. Robert Vance from MIT on lithography techniques and CMOS scaling challenges. Video recordings and slides are now archived in the digital library.",
            "pub_offset": -20,
            "exp_offset": -5,
            "priority": "Low",
            "audience": "Postgraduate (PG)",
            "department": "Department of Electronics",
        },
        {
            "title": "Annual Faculty & Staff Health Checkup Camp",
            "category": "Administrative",
            "description": "Comprehensive cardiac, ophthalmic, and dental checkup camp conducted by Apollo Hospitals on campus. Over 200 staff and faculty members completed their annual screening.",
            "pub_offset": -38,
            "exp_offset": -16,
            "priority": "Low",
            "audience": "Faculty & Staff",
            "department": "Campus Health Centre",
        },
    ]

    notices: List[Dict[str, Any]] = []
    for idx, item in enumerate(samples_blueprint, start=1):
        pub_d = anchor_date + timedelta(days=item["pub_offset"])
        exp_d = anchor_date + timedelta(days=item["exp_offset"])
        status, days, label, warning = compute_notice_status(pub_d, exp_d, anchor_date)

        notices.append(
            {
                "id": f"NOT-{idx:03d}",
                "title": item["title"],
                "category": item["category"],
                "description": item["description"],
                "published_date": pub_d.strftime("%Y-%m-%d"),
                "expiry_date": exp_d.strftime("%Y-%m-%d"),
                "priority": item["priority"],
                "audience": item["audience"],
                "department": item["department"],
                "status": status,
                "days_count": days,
                "time_label": label,
                "deadline_warning": warning,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    return notices


class NoticeDataManager:
    """
    Central manager for reading, writing, filtering, validating, and bulk importing notices
    with atomic JSON persistence, CSV synchronization, and automatic backup protection.
    """

    def __init__(self) -> None:
        ensure_data_directory()
        self.json_path = NOTICES_JSON_FILE
        self.csv_path = NOTICES_CSV_FILE
        self.backup_path = NOTICES_BACKUP_FILE
        self._ensure_sample_data()

    def _ensure_sample_data(self) -> None:
        """Check if local data file exists; if not, populate with 32 sample notices."""
        if not self.json_path.exists() or os.path.getsize(self.json_path) == 0:
            sample_notices = generate_sample_notices()
            self._save_to_disk(sample_notices)
            logger.info("Initialized default sample notices database.")

    def _save_to_disk(self, notices: List[Dict[str, Any]]) -> None:
        """
        Persist notices to JSON and CSV safely:
        1. Back up existing JSON file to notices.json.bak.
        2. Write to a temporary file first, then atomically replace.
        """
        ensure_data_directory()

        try:
            # Create safety backup if primary JSON exists and is non-empty
            if self.json_path.exists() and os.path.getsize(self.json_path) > 0:
                shutil.copy2(self.json_path, self.backup_path)

            # Atomic JSON write
            temp_json = self.json_path.with_suffix(".tmp")
            with open(temp_json, "w", encoding="utf-8") as f:
                json.dump(notices, f, indent=4, ensure_ascii=False)
            temp_json.replace(self.json_path)

            # Atomic CSV write
            df = pd.DataFrame(notices)
            temp_csv = self.csv_path.with_suffix(".tmp")
            df.to_csv(temp_csv, index=False, encoding="utf-8")
            temp_csv.replace(self.csv_path)

        except Exception as e:
            logger.error(f"Critical error saving notices to disk: {e}")
            raise

    def reset_to_sample_data(self) -> List[Dict[str, Any]]:
        """Reset storage back to a fresh realistic sample set."""
        sample_notices = generate_sample_notices(date.today())
        self._save_to_disk(sample_notices)
        logger.info(f"Database reset to sample notices ({len(sample_notices)} records).")
        return sample_notices

    def get_all_notices(self, recalculate_status: bool = True) -> List[Dict[str, Any]]:
        """
        Load all notices. If recalculate_status is True, dynamically updates
        notice status, days_count, relative time label, and deadline warnings.
        """
        if not self.json_path.exists():
            self._ensure_sample_data()

        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                notices = json.load(f)
        except Exception as e:
            logger.warning(f"Error reading JSON database ({e}). Attempting recovery from backup...")
            if self.backup_path.exists() and os.path.getsize(self.backup_path) > 0:
                shutil.copy2(self.backup_path, self.json_path)
                with open(self.json_path, "r", encoding="utf-8") as f:
                    notices = json.load(f)
            else:
                notices = generate_sample_notices()
                self._save_to_disk(notices)

        if recalculate_status:
            today = date.today()
            updated = False
            for notice in notices:
                new_status, days, label, warning = compute_notice_status(
                    notice.get("published_date", ""),
                    notice.get("expiry_date", ""),
                    today,
                )
                if (
                    notice.get("status") != new_status
                    or notice.get("days_count") != days
                    or notice.get("time_label") != label
                    or notice.get("deadline_warning") != warning
                ):
                    notice["status"] = new_status
                    notice["days_count"] = days
                    notice["time_label"] = label
                    notice["deadline_warning"] = warning
                    updated = True

            if updated:
                self._save_to_disk(notices)

        return notices

    def get_notice_by_id(self, notice_id: str) -> Optional[Dict[str, Any]]:
        """Find a specific notice by its unique ID."""
        notices = self.get_all_notices()
        for notice in notices:
            if notice["id"] == notice_id:
                return notice
        return None

    def add_notice(self, notice_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validate and insert a new notice with duplicate checking.
        Returns:
            (success, message, created_notice_dict)
        """
        notices = self.get_all_notices()

        # Input Validation & Duplicate Checking
        is_valid, error = validate_notice_input(
            title=notice_data.get("title", ""),
            description=notice_data.get("description", ""),
            category=notice_data.get("category", ""),
            published_date=notice_data.get("published_date"),
            expiry_date=notice_data.get("expiry_date"),
            priority=notice_data.get("priority", "Medium"),
            audience=notice_data.get("audience", "All Students"),
            department=notice_data.get("department", ""),
            existing_notices=notices,
        )

        if not is_valid:
            logger.warning(f"Failed to add notice: {error}")
            return False, error or "Validation failed.", None

        # Generate unique ID: NOT-001 format
        max_num = 0
        for n in notices:
            nid = n.get("id", "")
            if nid.startswith("NOT-"):
                try:
                    num = int(nid.split("-")[1])
                    if num > max_num:
                        max_num = num
                except ValueError:
                    pass
        new_id = f"NOT-{max_num + 1:03d}"

        # Standardize dates
        pub_date = notice_data["published_date"]
        if isinstance(pub_date, (date, datetime)):
            pub_date = pub_date.strftime("%Y-%m-%d")

        exp_date = notice_data["expiry_date"]
        if isinstance(exp_date, (date, datetime)):
            exp_date = exp_date.strftime("%Y-%m-%d")

        status, days, label, warning = compute_notice_status(pub_date, exp_date)

        new_notice = {
            "id": new_id,
            "title": notice_data["title"].strip(),
            "category": notice_data["category"],
            "description": notice_data["description"].strip(),
            "published_date": pub_date,
            "expiry_date": exp_date,
            "priority": notice_data.get("priority", "Medium"),
            "audience": notice_data.get("audience", "All Students"),
            "department": notice_data.get("department", "College Administration").strip(),
            "status": status,
            "days_count": days,
            "time_label": label,
            "deadline_warning": warning,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Insert at the beginning so latest notices show first
        notices.insert(0, new_notice)
        self._save_to_disk(notices)
        logger.info(f"Notice created: {new_id} - '{new_notice['title']}' ({new_notice['category']}, {new_notice['priority']})")
        return True, f"Notice '{new_notice['title']}' created successfully with ID {new_id}!", new_notice

    def update_notice(
        self, notice_id: str, updated_data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validate and update an existing notice with duplicate checking.
        Returns:
            (success, message, updated_notice_dict)
        """
        notices = self.get_all_notices()
        found_idx = None
        for idx, n in enumerate(notices):
            if n["id"] == notice_id:
                found_idx = idx
                break

        if found_idx is None:
            logger.warning(f"Update failed: Notice ID {notice_id} not found.")
            return False, f"Notice with ID {notice_id} was not found.", None

        # Input Validation & Duplicate Checking against other notices
        is_valid, error = validate_notice_input(
            title=updated_data.get("title", ""),
            description=updated_data.get("description", ""),
            category=updated_data.get("category", ""),
            published_date=updated_data.get("published_date"),
            expiry_date=updated_data.get("expiry_date"),
            priority=updated_data.get("priority", "Medium"),
            audience=updated_data.get("audience", "All Students"),
            department=updated_data.get("department", ""),
            existing_notices=notices,
            exclude_id=notice_id,
        )

        if not is_valid:
            logger.warning(f"Update rejected for {notice_id}: {error}")
            return False, error or "Validation failed.", None

        pub_date = updated_data["published_date"]
        if isinstance(pub_date, (date, datetime)):
            pub_date = pub_date.strftime("%Y-%m-%d")

        exp_date = updated_data["expiry_date"]
        if isinstance(exp_date, (date, datetime)):
            exp_date = exp_date.strftime("%Y-%m-%d")

        status, days, label, warning = compute_notice_status(pub_date, exp_date)

        target = notices[found_idx]
        target["title"] = updated_data["title"].strip()
        target["category"] = updated_data["category"]
        target["description"] = updated_data["description"].strip()
        target["published_date"] = pub_date
        target["expiry_date"] = exp_date
        target["priority"] = updated_data.get("priority", target.get("priority", "Medium"))
        target["audience"] = updated_data.get("audience", target.get("audience", "All Students"))
        target["department"] = updated_data.get("department", target.get("department", "Administration")).strip()
        target["status"] = status
        target["days_count"] = days
        target["time_label"] = label
        target["deadline_warning"] = warning
        target["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        notices[found_idx] = target
        self._save_to_disk(notices)
        logger.info(f"Notice updated: {notice_id} - '{target['title']}'")
        return True, f"Notice {notice_id} updated successfully!", target

    def delete_notice(self, notice_id: str) -> Tuple[bool, str]:
        """
        Delete a notice by ID.
        Returns:
            (success, message)
        """
        notices = self.get_all_notices()
        initial_count = len(notices)
        filtered = [n for n in notices if n["id"] != notice_id]

        if len(filtered) == initial_count:
            logger.warning(f"Delete failed: Notice ID {notice_id} does not exist.")
            return False, f"Notice with ID {notice_id} does not exist."

        self._save_to_disk(filtered)
        logger.info(f"Notice deleted: {notice_id}")
        return True, f"Notice {notice_id} was successfully deleted."

    def import_notices_from_csv(
        self, csv_file_or_content: Any
    ) -> Dict[str, Any]:
        """
        Bulk import notices from a CSV file or buffer with granular row-by-row
        validation, duplicate checks, and explicit error reporting.

        Returns dict:
            {
                "success_count": int,
                "fail_count": int,
                "imported_notices": List[Dict],
                "errors": List[Dict[str, Any]] (row, title, reason)
            }
        """
        errors: List[Dict[str, Any]] = []
        valid_to_add: List[Dict[str, Any]] = []

        try:
            if hasattr(csv_file_or_content, "read"):
                # File-like object (e.g. from st.file_uploader)
                content = csv_file_or_content.read()
                if isinstance(content, bytes):
                    content = content.decode("utf-8", errors="replace")
                reader = csv.DictReader(io.StringIO(content))
            elif isinstance(csv_file_or_content, str):
                reader = csv.DictReader(io.StringIO(csv_file_or_content))
            else:
                return {
                    "success_count": 0,
                    "fail_count": 1,
                    "imported_notices": [],
                    "errors": [{"row": 0, "title": "N/A", "reason": "Invalid CSV file format provided."}],
                }
        except Exception as e:
            logger.error(f"Failed to parse CSV file: {e}")
            return {
                "success_count": 0,
                "fail_count": 1,
                "imported_notices": [],
                "errors": [{"row": 0, "title": "N/A", "reason": f"CSV parse error: {str(e)}"}],
            }

        # Normalize field headers (lower, strip)
        if not reader.fieldnames:
            return {
                "success_count": 0,
                "fail_count": 1,
                "imported_notices": [],
                "errors": [{"row": 0, "title": "N/A", "reason": "CSV file is empty or has no header row."}],
            }

        current_notices = self.get_all_notices()
        batch_seen_titles: set = set()

        # Find maximum existing ID
        max_num = 0
        for n in current_notices:
            nid = n.get("id", "")
            if nid.startswith("NOT-"):
                try:
                    num = int(nid.split("-")[1])
                    if num > max_num:
                        max_num = num
                except ValueError:
                    pass

        row_num = 1
        for row in reader:
            row_num += 1
            # Normalize row keys
            norm_row = {k.strip().lower().replace(" ", "_"): (v or "").strip() for k, v in row.items() if k}

            title = norm_row.get("title", "")
            desc = norm_row.get("description", "")
            cat = norm_row.get("category", "")
            pub = norm_row.get("published_date", "")
            exp = norm_row.get("expiry_date", "")
            pri = norm_row.get("priority", "Medium")
            aud = norm_row.get("audience", norm_row.get("target_audience", "All Students"))
            dept = norm_row.get("department", "College Administration")

            # Check intra-batch duplicate
            norm_t = normalize_title(title)
            batch_key = (norm_t, cat)
            if batch_key in batch_seen_titles:
                errors.append({
                    "row": row_num,
                    "title": title or "Untitled",
                    "reason": "Duplicate notice within the uploaded CSV file itself."
                })
                continue

            # Validate row
            is_valid, err_msg = validate_notice_input(
                title=title,
                description=desc,
                category=cat,
                published_date=pub,
                expiry_date=exp,
                priority=pri if pri in PRIORITIES else "Medium",
                audience=aud if aud in AUDIENCES else "All Students",
                department=dept,
                existing_notices=current_notices + valid_to_add,
            )

            if not is_valid:
                errors.append({
                    "row": row_num,
                    "title": title or f"Row {row_num}",
                    "reason": err_msg or "Validation error.",
                })
                continue

            # Construct valid notice
            max_num += 1
            new_id = f"NOT-{max_num:03d}"
            status, days, label, warning = compute_notice_status(pub, exp)

            notice_obj = {
                "id": new_id,
                "title": title,
                "category": cat,
                "description": desc,
                "published_date": pub[:10],
                "expiry_date": exp[:10],
                "priority": pri if pri in PRIORITIES else "Medium",
                "audience": aud if aud in AUDIENCES else "All Students",
                "department": dept or "College Administration",
                "status": status,
                "days_count": days,
                "time_label": label,
                "deadline_warning": warning,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            batch_seen_titles.add(batch_key)
            valid_to_add.append(notice_obj)

        if valid_to_add:
            # Prepend imported notices to database
            all_updated = valid_to_add + current_notices
            self._save_to_disk(all_updated)
            logger.info(f"Bulk CSV import complete: {len(valid_to_add)} added, {len(errors)} rejected.")

        return {
            "success_count": len(valid_to_add),
            "fail_count": len(errors),
            "imported_notices": valid_to_add,
            "errors": errors,
        }

    def filter_notices(
        self,
        notices: List[Dict[str, Any]],
        search_query: str = "",
        category: str = "All",
        status: str = "All",
        priority: str = "All",
        audience: str = "All",
        sort_by: str = "Published Date (Newest)",
    ) -> List[Dict[str, Any]]:
        """
        Multi-criteria search, filtering, and sorting across all notice fields.
        """
        result = notices

        # Search filter (matches title, description, category, department, audience, or ID)
        if search_query and search_query.strip():
            tokens = search_query.strip().lower().split()
            filtered = []
            for n in result:
                searchable = (
                    f"{n.get('id', '')} {n.get('title', '')} {n.get('description', '')} "
                    f"{n.get('department', '')} {n.get('category', '')} {n.get('audience', '')}"
                ).lower()
                # All search tokens must be present
                if all(t in searchable for t in tokens):
                    filtered.append(n)
            result = filtered

        # Category filter
        if category and category != "All":
            result = [n for n in result if n.get("category") == category]

        # Status filter
        if status and status != "All":
            result = [n for n in result if n.get("status") == status]

        # Priority filter
        if priority and priority != "All":
            result = [n for n in result if n.get("priority") == priority]

        # Audience filter
        if audience and audience != "All":
            result = [n for n in result if n.get("audience") == audience]

        # Sorting
        if sort_by == "Published Date (Newest)":
            result = sorted(result, key=lambda x: x.get("published_date", ""), reverse=True)
        elif sort_by == "Published Date (Oldest)":
            result = sorted(result, key=lambda x: x.get("published_date", ""))
        elif sort_by == "Expiry Date (Earliest / Soonest)":
            result = sorted(result, key=lambda x: x.get("expiry_date", ""))
        elif sort_by == "Expiry Date (Latest)":
            result = sorted(result, key=lambda x: x.get("expiry_date", ""), reverse=True)
        elif sort_by == "Priority (Critical to Low)":
            priority_rank = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
            result = sorted(result, key=lambda x: priority_rank.get(x.get("priority", "Medium"), 2))
        elif sort_by == "Title (A-Z)":
            result = sorted(result, key=lambda x: x.get("title", "").lower())
        elif sort_by == "Title (Z-A)":
            result = sorted(result, key=lambda x: x.get("title", "").lower(), reverse=True)

        return result

    def get_dashboard_metrics(self, notices: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Calculate summary counts, alerts, urgent notices, and status metrics.
        """
        if notices is None:
            notices = self.get_all_notices()

        total = len(notices)
        active = sum(1 for n in notices if n.get("status") == STATUS_ACTIVE)
        expired = sum(1 for n in notices if n.get("status") == STATUS_EXPIRED)
        upcoming = sum(1 for n in notices if n.get("status") == STATUS_UPCOMING)

        # Critical priority notices
        critical_all = [n for n in notices if n.get("priority") == "Critical"]
        critical_active = [n for n in critical_all if n.get("status") == STATUS_ACTIVE]

        # Notices expiring soon (Active and expires in <= 3 days)
        expiring_soon = [
            n for n in notices if n.get("status") == STATUS_ACTIVE and 0 <= n.get("days_count", 999) <= 3
        ]

        # Upcoming releases scheduled within next 3 days
        upcoming_soon = [
            n for n in notices if n.get("status") == STATUS_UPCOMING and 1 <= n.get("days_count", 999) <= 3
        ]

        # Urgent notices (Critical/High Active or Closing within 48 hours)
        urgent = [
            n for n in notices
            if n.get("status") == STATUS_ACTIVE and (
                n.get("priority") in ("Critical", "High") or n.get("days_count", 999) <= 2
            )
        ]

        return {
            "total": total,
            "active": active,
            "expired": expired,
            "upcoming": upcoming,
            "critical_count": len(critical_all),
            "critical_active": critical_active,
            "expiring_soon": expiring_soon,
            "expiring_soon_count": len(expiring_soon),
            "upcoming_soon": upcoming_soon,
            "urgent": urgent,
            "urgent_count": len(urgent),
        }

    def get_monthly_statistics(self, notices: Optional[List[Dict[str, Any]]] = None) -> pd.DataFrame:
        """
        Generate monthly notice activity statistics (notices published per month).
        """
        if notices is None:
            notices = self.get_all_notices()

        if not notices:
            return pd.DataFrame(columns=["Month", "Total Published", "Active", "Upcoming", "Expired"])

        rows = []
        for n in notices:
            pub_date = n.get("published_date", "")[:7]  # YYYY-MM
            if pub_date:
                rows.append({"month": pub_date, "status": n.get("status", "")})

        if not rows:
            return pd.DataFrame(columns=["Month", "Total Published", "Active", "Upcoming", "Expired"])

        df_raw = pd.DataFrame(rows)
        grouped = df_raw.groupby("month").agg(
            Total_Published=("status", "count"),
            Active=("status", lambda s: (s == STATUS_ACTIVE).sum()),
            Upcoming=("status", lambda s: (s == STATUS_UPCOMING).sum()),
            Expired=("status", lambda s: (s == STATUS_EXPIRED).sum()),
        ).reset_index()

        grouped.rename(columns={"month": "Month", "Total_Published": "Total Published"}, inplace=True)
        grouped.sort_values(by="Month", inplace=True)
        return grouped

    def get_category_analytics(self, notices: Optional[List[Dict[str, Any]]] = None) -> pd.DataFrame:
        """
        Generate comprehensive category-wise breakdown table.
        """
        if notices is None:
            notices = self.get_all_notices()

        if not notices:
            return pd.DataFrame(columns=["Category", "Total Notices", "Active", "Upcoming", "Expired", "Critical & High"])

        df = pd.DataFrame(notices)
        cat_stats = []
        for cat in CATEGORIES:
            sub = df[df["category"] == cat]
            total = len(sub)
            act = (sub["status"] == STATUS_ACTIVE).sum() if total > 0 else 0
            upc = (sub["status"] == STATUS_UPCOMING).sum() if total > 0 else 0
            exp = (sub["status"] == STATUS_EXPIRED).sum() if total > 0 else 0
            crit_high = (sub["priority"].isin(["Critical", "High"])).sum() if total > 0 else 0

            cat_stats.append({
                "Category": cat,
                "Total Notices": total,
                "Active": act,
                "Upcoming": upc,
                "Expired": exp,
                "Critical & High": crit_high,
            })

        return pd.DataFrame(cat_stats)

    def get_dataframe(self, notices: Optional[List[Dict[str, Any]]] = None) -> pd.DataFrame:
        """Convert notices to a structured pandas DataFrame for display or export."""
        if notices is None:
            notices = self.get_all_notices()

        if not notices:
            return pd.DataFrame(
                columns=[
                    "id",
                    "title",
                    "category",
                    "status",
                    "priority",
                    "audience",
                    "department",
                    "published_date",
                    "expiry_date",
                    "time_label",
                    "deadline_warning",
                    "description",
                ]
            )

        df = pd.DataFrame(notices)
        return df

    def export_to_csv_bytes(self, notices: Optional[List[Dict[str, Any]]] = None) -> bytes:
        """Export notice list to CSV bytes for Streamlit download button."""
        df = self.get_dataframe(notices)
        return df.to_csv(index=False).encode("utf-8")

    def export_to_json_bytes(self, notices: Optional[List[Dict[str, Any]]] = None) -> bytes:
        """Export notice list to JSON bytes for download."""
        if notices is None:
            notices = self.get_all_notices()
        return json.dumps(notices, indent=4, ensure_ascii=False).encode("utf-8")

    def get_recent_logs(self, limit: int = 50) -> List[str]:
        """Read recent timestamped application log lines."""
        if not APP_LOG_FILE.exists():
            return ["No log entries recorded yet."]
        try:
            with open(APP_LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            return [line.strip() for line in lines[-limit:]]
        except Exception as e:
            return [f"Could not read log file: {e}"]
