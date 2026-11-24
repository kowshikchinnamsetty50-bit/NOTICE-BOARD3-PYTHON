"""
Configuration and constants for the Notice Board Organizer application.
"""

from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
NOTICES_JSON_FILE = DATA_DIR / "notices.json"
NOTICES_CSV_FILE = DATA_DIR / "notices.csv"
NOTICES_BACKUP_FILE = DATA_DIR / "notices.json.bak"
APP_LOG_FILE = DATA_DIR / "app.log"

# College Branding & Portal Details
APP_TITLE = "CampusPulse"
APP_SUBTITLE = "College Notice Board Organizer"
COLLEGE_NAME = "National Institute of Science & Technology"

# Notice Categories with Icons
CATEGORIES = [
    "Academics",
    "Examinations",
    "Placements & Internships",
    "Events & Cultural",
    "Sports & Athletics",
    "Scholarships & Aid",
    "Campus & Hostel",
    "Administrative",
]

CATEGORY_ICONS = {
    "Academics": "📚",
    "Examinations": "📝",
    "Placements & Internships": "💼",
    "Events & Cultural": "🎭",
    "Sports & Athletics": "🏆",
    "Scholarships & Aid": "🎓",
    "Campus & Hostel": "🏢",
    "Administrative": "🏛️",
}

CATEGORY_COLORS = {
    "Academics": "#2563EB",            # Royal Blue
    "Examinations": "#DC2626",         # Crimson
    "Placements & Internships": "#059669", # Emerald Green
    "Events & Cultural": "#7C3AED",    # Purple
    "Sports & Athletics": "#D97706",   # Amber / Orange
    "Scholarships & Aid": "#0891B2",   # Cyan / Teal
    "Campus & Hostel": "#4B5563",      # Cool Gray
    "Administrative": "#4F46E5",       # Indigo
}

# Priority Levels (Critical, High, Medium, Low)
PRIORITIES = ["Critical", "High", "Medium", "Low"]

PRIORITY_COLORS = {
    "Critical": "#991B1B", # Deep Crimson / Alarm
    "High": "#DC2626",     # Red
    "Medium": "#D97706",   # Amber
    "Low": "#2563EB",      # Blue
}

PRIORITY_BADGES = {
    "Critical": "🚨 Critical",
    "High": "🔴 High",
    "Medium": "🟡 Medium",
    "Low": "🔵 Low",
}

# Target Audiences / Departments
AUDIENCES = [
    "All Students",
    "Undergraduate (UG)",
    "Postgraduate (PG)",
    "Final Year Students",
    "Hostellers & Residents",
    "Faculty & Staff",
]

# Notice Status Constants
STATUS_ACTIVE = "Active"
STATUS_UPCOMING = "Upcoming"
STATUS_EXPIRED = "Expired"

STATUS_OPTIONS = [STATUS_ACTIVE, STATUS_UPCOMING, STATUS_EXPIRED]

STATUS_COLORS = {
    STATUS_ACTIVE: "#10B981",    # Bright Emerald Green
    STATUS_UPCOMING: "#3B82F6",  # Bright Blue
    STATUS_EXPIRED: "#9CA3AF",   # Muted Slate Gray
}

STATUS_ICONS = {
    STATUS_ACTIVE: "🟢",
    STATUS_UPCOMING: "🔵",
    STATUS_EXPIRED: "⚪",
}
