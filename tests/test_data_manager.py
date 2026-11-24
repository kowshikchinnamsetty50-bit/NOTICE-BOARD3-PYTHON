"""
Comprehensive unit test suite for CampusPulse Notice Board Organizer.
Tests CRUD operations, duplicate prevention, validation, status calculations,
CSV bulk import with error reporting, and backup reliability.
"""

import os
import sys
from datetime import date, timedelta
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.data_manager import NoticeDataManager, compute_notice_status, validate_notice_input
from config import NOTICES_BACKUP_FILE, APP_LOG_FILE


def run_all_tests():
    print("==================================================")
    print("  Running Notice Board Organizer Test Suite")
    print("==================================================")

    dm = NoticeDataManager()
    notices = dm.get_all_notices()
    print(f"[1] Loaded {len(notices)} notices successfully.")
    assert len(notices) >= 30, f"Expected >= 30 sample notices, got {len(notices)}"

    # 1. Test Status Calculations
    today = date.today()
    status_act, days_act, lbl_act, warn_act = compute_notice_status(today - timedelta(days=2), today + timedelta(days=5), today)
    assert status_act == "Active", f"Expected Active, got {status_act}"
    print(f"[2] Active status computation verified: {status_act} ({lbl_act})")

    status_upc, days_upc, lbl_upc, warn_upc = compute_notice_status(today + timedelta(days=4), today + timedelta(days=10), today)
    assert status_upc == "Upcoming", f"Expected Upcoming, got {status_upc}"
    print(f"[3] Upcoming status computation verified: {status_upc} ({lbl_upc})")

    status_exp, days_exp, lbl_exp, warn_exp = compute_notice_status(today - timedelta(days=15), today - timedelta(days=3), today)
    assert status_exp == "Expired", f"Expected Expired, got {status_exp}"
    print(f"[4] Expired status computation verified: {status_exp} ({lbl_exp})")

    # 2. Test Input Validation & Date Constraints
    # Invalid: Expiry before published
    valid, err = validate_notice_input("Valid Title", "Valid description that is long enough", "Academics", today, today - timedelta(days=1))
    assert not valid and "cannot be earlier" in err, f"Expected expiry date error, got: {err}"
    print("[5] Expiry before published date rejected correctly.")

    # Invalid: Empty title
    valid, err = validate_notice_input("", "Valid description that is long enough", "Academics", today, today + timedelta(days=5))
    assert not valid and "empty" in err, f"Expected empty title error, got: {err}"
    print("[6] Empty title rejected correctly.")

    # Invalid: Short description
    valid, err = validate_notice_input("Valid Title", "Short", "Academics", today, today + timedelta(days=5))
    assert not valid and "at least 10" in err, f"Expected short description error, got: {err}"
    print("[7] Short description rejected correctly.")

    # 3. Test Add Notice with Critical Priority
    res_add, msg_add, item_add = dm.add_notice({
        "title": "Emergency Server Maintenance Notice 2026",
        "category": "Administrative",
        "description": "All campus IT services and ERP servers will be offline for high-priority emergency patches.",
        "published_date": today.strftime("%Y-%m-%d"),
        "expiry_date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
        "priority": "Critical",
        "audience": "All Students",
        "department": "Campus IT Centre",
    })
    assert res_add is True, f"Failed to add notice: {msg_add}"
    assert item_add["priority"] == "Critical", "Expected Critical priority"
    print(f"[8] Added Critical priority notice: {item_add['id']} - {item_add['title']}")

    # 4. Test Duplicate Notice Prevention
    res_dup, msg_dup, _ = dm.add_notice({
        "title": "Emergency Server Maintenance Notice 2026",
        "category": "Administrative",
        "description": "Another identical attempt to create duplicate notice.",
        "published_date": today.strftime("%Y-%m-%d"),
        "expiry_date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
        "priority": "Critical",
        "audience": "All Students",
        "department": "Campus IT Centre",
    })
    assert res_dup is False and "Duplicate" in msg_dup, f"Expected duplicate rejection, got: {msg_dup}"
    print(f"[9] Duplicate notice prevented successfully: {msg_dup}")

    # 5. Test Update Notice
    res_up, msg_up, item_up = dm.update_notice(item_add["id"], {
        "title": "Updated Emergency Server Maintenance Notice 2026",
        "category": "Administrative",
        "description": "Updated description with extended maintenance window details.",
        "published_date": today.strftime("%Y-%m-%d"),
        "expiry_date": (today + timedelta(days=3)).strftime("%Y-%m-%d"),
        "priority": "Critical",
        "audience": "All Students",
        "department": "Campus IT Centre",
    })
    assert res_up is True, f"Failed to update: {msg_up}"
    print(f"[10] Notice updated successfully: {item_up['title']}")

    # 6. Test Delete Notice
    res_del, msg_del = dm.delete_notice(item_add["id"])
    assert res_del is True, f"Failed to delete: {msg_del}"
    print(f"[11] Notice deleted successfully: {item_add['id']}")

    # 7. Test Bulk CSV Import with Error Reporting
    csv_payload = (
        "title,category,description,published_date,expiry_date,priority,audience,department\n"
        "Inter-College Chess Fest,Sports & Athletics,Championship tournament open for all undergraduate participants.,2026-11-20,2026-12-05,Medium,All Students,Sports Department\n"
        "Bad Row Early Expiry,Academics,This row should fail validation due to invalid dates.,2026-12-10,2026-11-01,Low,All Students,Academics Office\n"
        "Bad Row Short Desc,Examinations,Too short,2026-11-20,2026-12-05,High,All Students,Examinations Office\n"
    )
    import_res = dm.import_notices_from_csv(csv_payload)
    assert import_res["success_count"] == 1, f"Expected 1 success, got {import_res['success_count']}"
    assert import_res["fail_count"] == 2, f"Expected 2 fails, got {import_res['fail_count']}"
    print(f"[12] CSV Bulk Import verified: {import_res['success_count']} succeeded, {import_res['fail_count']} rejected with explicit error reporting.")

    # Clean up imported notice
    if import_res["imported_notices"]:
        for n in import_res["imported_notices"]:
            dm.delete_notice(n["id"])

    # 8. Test Backup File Creation
    assert NOTICES_BACKUP_FILE.exists() and os.path.getsize(NOTICES_BACKUP_FILE) > 0, "Expected notices.json.bak to exist"
    print(f"[13] Safety backup file verified: {NOTICES_BACKUP_FILE.name}")

    # 9. Test Application Logging
    assert APP_LOG_FILE.exists() and os.path.getsize(APP_LOG_FILE) > 0, "Expected app.log to exist"
    logs = dm.get_recent_logs(5)
    assert len(logs) > 0, "Expected log entries"
    print(f"[14] Application logger verified ({len(logs)} recent entries found).")

    # 10. Test Analytics
    monthly_stats = dm.get_monthly_statistics()
    assert not monthly_stats.empty, "Expected monthly stats DataFrame"
    cat_analytics = dm.get_category_analytics()
    assert not cat_analytics.empty, "Expected category analytics DataFrame"
    print("[15] Monthly statistics and category analytics generated successfully.")

    print("\n==================================================")
    print("  ALL 15 TESTS PASSED SUCCESSFULLY! (100% SUCCESS) ")
    print("==================================================")


if __name__ == "__main__":
    run_all_tests()
