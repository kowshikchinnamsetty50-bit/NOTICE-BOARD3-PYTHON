"""
CampusPulse: College Notice Board Organizer
Main Application Entry Point built with Streamlit.
Upgraded with Critical priorities, bulk CSV import, duplicate notice prevention,
monthly analytics, and timestamped audit logging.
"""

import io
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st

from config import (
    APP_SUBTITLE,
    APP_TITLE,
    AUDIENCES,
    CATEGORIES,
    CATEGORY_ICONS,
    COLLEGE_NAME,
    PRIORITIES,
    PRIORITY_BADGES,
    STATUS_ACTIVE,
    STATUS_EXPIRED,
    STATUS_OPTIONS,
    STATUS_UPCOMING,
)
from modules.data_manager import (
    NoticeDataManager,
    check_duplicate_notice,
    compute_notice_status,
)
from modules.ui_components import (
    inject_custom_css,
    render_category_chart,
    render_dashboard_metrics,
    render_monthly_chart,
    render_notice_card_html,
    render_portal_header,
    render_priority_badge_html,
    render_status_badge_html,
    render_status_chart,
)

# Set Streamlit Page Configuration
st.set_page_config(
    page_title=f"{APP_TITLE} | {APP_SUBTITLE}",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply Custom CSS
inject_custom_css()


# Initialize Data Manager
@st.cache_resource
def get_data_manager() -> NoticeDataManager:
    return NoticeDataManager()


dm = get_data_manager()


def sidebar_navigation() -> str:
    """Render the sidebar branding and navigation menu."""
    st.sidebar.markdown(
        f"""
        <div style="text-align: center; padding: 12px 0 16px 0; border-bottom: 1px solid #E2E8F0;">
            <div style="font-size: 38px; line-height: 1;">🏛️</div>
            <h2 style="margin: 8px 0 2px 0; font-size: 20px; font-weight: 800; color: #1E3A8A;">{APP_TITLE}</h2>
            <p style="margin: 0; font-size: 11px; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Campus Notice Board</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("### 📌 Navigation")
    menu_options = [
        "📊 Dashboard",
        "📋 Browse & Search Notices",
        "➕ Add New Notice",
        "📥 Bulk CSV Import",
        "✏️ Edit & Manage Notices",
        "📑 Reports & Analytics",
        "ℹ️ User Guide & Logs",
    ]

    if "current_page" not in st.session_state:
        st.session_state["current_page"] = menu_options[0]

    selected = st.sidebar.radio(
        "Go to page:",
        options=menu_options,
        index=menu_options.index(st.session_state["current_page"])
        if st.session_state["current_page"] in menu_options
        else 0,
        label_visibility="collapsed",
    )
    st.session_state["current_page"] = selected

    # Quick summary in sidebar
    metrics = dm.get_dashboard_metrics()
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### ⚡ Quick Pulse")
    col_a, col_b = st.sidebar.columns(2)
    col_a.metric("Active", metrics["active"])
    col_b.metric("Upcoming", metrics["upcoming"])

    st.sidebar.markdown(
        f"""
        <div class="sidebar-card">
            <strong>🏫 {COLLEGE_NAME}</strong><br/>
            Session: 2026–2027<br/>
            Storage: <code>JSON + CSV Dual Sync</code><br/>
            Backup: <code>notices.json.bak</code><br/>
            <span style="color: #059669; font-weight: 600;">● System Active</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return selected


# ==============================================================================
# PAGE 1: DASHBOARD
# ==============================================================================
def page_dashboard() -> None:
    render_portal_header()
    notices = dm.get_all_notices()
    metrics = dm.get_dashboard_metrics(notices)

    # 1. Metric Cards
    render_dashboard_metrics(metrics)
    st.write("")

    # 2. Urgent Attention Alerts
    critical_active = metrics.get("critical_active", [])
    if critical_active:
        crit_titles = " • ".join([f"<strong>{n['title']}</strong>" for n in critical_active[:3]])
        st.markdown(
            f"""
            <div class="alert-box critical-alert">
                <strong>🚨 CRITICAL ACTION REQUIRED ({len(critical_active)} notice{'s' if len(critical_active) != 1 else ''}):</strong><br/>
                {crit_titles}
            </div>
            """,
            unsafe_allow_html=True,
        )

    expiring = metrics.get("expiring_soon", [])
    if expiring:
        st.markdown(
            f"""
            <div class="alert-box">
                <strong>⚠️ Approaching Deadlines:</strong>
                There {'is' if len(expiring) == 1 else 'are'} <strong>{len(expiring)} active notice{'s' if len(expiring) != 1 else ''}</strong>
                expiring within the next 3 days. Please review and complete necessary filings before links close.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 3. Visual Charts Section
    col_chart1, col_chart2 = st.columns([1.5, 1])
    with col_chart1:
        st.markdown("#### 📊 Notices by Category")
        render_category_chart(notices)

    with col_chart2:
        st.markdown("#### 🎯 Status Breakdown")
        render_status_chart(notices)

    # Monthly Trend
    monthly_df = dm.get_monthly_statistics(notices)
    if not monthly_df.empty:
        st.markdown("#### 📈 Monthly Publication Activity")
        render_monthly_chart(monthly_df)

    st.markdown("---")

    # 4. Featured Urgent & Critical Active Notices
    urgent_items = metrics.get("urgent", [])
    if urgent_items:
        st.markdown("#### ⚡ Urgent & High Priority Action Items")
        for n in urgent_items[:3]:
            st.markdown(render_notice_card_html(n), unsafe_allow_html=True)

    # 5. Upcoming Releases Scheduled
    upcoming_soon = metrics.get("upcoming_soon", [])
    if upcoming_soon:
        st.markdown("---")
        st.markdown("#### 🗓️ Upcoming Notices (Going Live Soon)")
        for n in upcoming_soon[:2]:
            st.markdown(render_notice_card_html(n), unsafe_allow_html=True)

    # 6. Recent Feed
    st.markdown("---")
    st.markdown("#### 🕒 Latest Published Notices")
    recent = sorted(notices, key=lambda x: x.get("published_date", ""), reverse=True)[:3]
    for n in recent:
        st.markdown(render_notice_card_html(n), unsafe_allow_html=True)


# ==============================================================================
# PAGE 2: BROWSE & SEARCH NOTICES
# ==============================================================================
def page_browse_notices() -> None:
    st.markdown("## 📋 Campus Notice Board")
    st.markdown("Search, filter, and view all college announcements.")

    notices = dm.get_all_notices()

    # Search & Filter Controls
    search_col, sort_col = st.columns([3, 1.5])
    with search_col:
        search_query = st.text_input(
            "🔍 Search notices by keyword, title, ID, category, or department:",
            placeholder="e.g. Exam, Placement, Hackathon, NOT-001, Library...",
        )
    with sort_col:
        sort_by = st.selectbox(
            "Sort by:",
            [
                "Published Date (Newest)",
                "Published Date (Oldest)",
                "Expiry Date (Earliest / Soonest)",
                "Expiry Date (Latest)",
                "Priority (Critical to Low)",
                "Title (A-Z)",
                "Title (Z-A)",
            ],
        )

    # Multi-facet filters
    with st.expander("🎯 Filter by Category, Status, Priority & Audience", expanded=False):
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1:
            cat_filter = st.selectbox("Category:", ["All"] + CATEGORIES)
        with f_col2:
            status_filter = st.selectbox("Status:", ["All"] + STATUS_OPTIONS)
        with f_col3:
            priority_filter = st.selectbox("Priority:", ["All"] + PRIORITIES)
        with f_col4:
            audience_filter = st.selectbox("Audience:", ["All"] + AUDIENCES)

    # Apply filters
    filtered = dm.filter_notices(
        notices=notices,
        search_query=search_query,
        category=cat_filter,
        status=status_filter,
        priority=priority_filter,
        audience=audience_filter,
        sort_by=sort_by,
    )

    # View layout selector and count badge
    c_left, c_right = st.columns([3, 1])
    with c_left:
        st.markdown(
            f"Showing **{len(filtered)}** of **{len(notices)}** notices "
            + (f"matching criteria" if len(filtered) != len(notices) else "")
        )
    with c_right:
        view_mode = st.radio("Display Mode:", ["Card View", "Table View"], horizontal=True)

    if not filtered:
        st.warning("No notices found matching your search and filter criteria. Try adjusting your filters.")
        return

    # Render results
    if view_mode == "Card View":
        for notice in filtered:
            st.markdown(render_notice_card_html(notice), unsafe_allow_html=True)
    else:
        # Table View
        df = dm.get_dataframe(filtered)
        display_df = df[
            [
                "id",
                "title",
                "category",
                "status",
                "priority",
                "audience",
                "published_date",
                "expiry_date",
                "time_label",
                "deadline_warning",
                "department",
            ]
        ].copy()
        display_df.rename(
            columns={
                "id": "Notice ID",
                "title": "Title",
                "category": "Category",
                "status": "Status",
                "priority": "Priority",
                "audience": "Target Audience",
                "published_date": "Published",
                "expiry_date": "Expires",
                "time_label": "Timeline",
                "deadline_warning": "Warning",
                "department": "Department",
            },
            inplace=True,
        )
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )


# ==============================================================================
# PAGE 3: ADD NEW NOTICE
# ==============================================================================
def page_add_notice() -> None:
    st.markdown("## ➕ Publish New Notice")
    st.markdown("Broadcast an official announcement to students, faculty, and departments.")

    today = date.today()
    notices = dm.get_all_notices()

    with st.form("add_notice_form", clear_on_submit=False):
        st.markdown("#### 1. Basic Notice Information")
        title = st.text_input(
            "Notice Title *",
            placeholder="e.g. Schedule for Mid-Term Examination 2026",
            help="Enter a clear, descriptive title between 3 and 120 characters.",
        )

        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox(
                "Notice Category *",
                CATEGORIES,
                format_func=lambda x: f"{CATEGORY_ICONS.get(x, '📌')} {x}",
            )
        with col2:
            priority = st.selectbox("Priority Level *", PRIORITIES, index=2)  # Default: Medium

        col3, col4 = st.columns(2)
        with col3:
            audience = st.selectbox("Target Audience *", AUDIENCES)
        with col4:
            department = st.text_input(
                "Issuing Department / Office *",
                value="Dean of Academic Affairs",
                help="The department or office authorizing this announcement.",
            )

        st.markdown("#### 2. Notice Dates (Controls Automatic Status)")
        st.caption(
            "💡 The system automatically determines whether this notice is **Active**, **Upcoming**, or **Expired** based on these dates relative to today."
        )

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            published_date = st.date_input(
                "Published Date *",
                value=today,
                help="Date when the notice becomes visible or takes effect.",
            )
        with col_d2:
            expiry_date = st.date_input(
                "Expiry Date (Deadline) *",
                value=today + timedelta(days=14),
                help="Date when the notice or application deadline concludes.",
            )

        st.markdown("#### 3. Notice Content")
        description = st.text_area(
            "Detailed Description / Announcement Body *",
            placeholder="Provide comprehensive details, instructions, links, eligibility criteria, venue, and relevant contacts...",
            height=160,
            help="Detailed notice text (minimum 10 characters, maximum 5,000 characters).",
        )

        submitted = st.form_submit_button("🚀 Publish Notice to Board", use_container_width=True)

    if submitted:
        new_data = {
            "title": title,
            "category": category,
            "description": description,
            "published_date": published_date,
            "expiry_date": expiry_date,
            "priority": priority,
            "audience": audience,
            "department": department,
        }

        success, message, created_item = dm.add_notice(new_data)
        if success and created_item:
            st.success(f"🎉 {message}")
            st.markdown("#### 👁️ Live Preview of Published Notice:")
            st.markdown(render_notice_card_html(created_item), unsafe_allow_html=True)
        else:
            st.error(f"❌ Could not publish notice: {message}")


# ==============================================================================
# PAGE 4: BULK CSV IMPORT
# ==============================================================================
def page_bulk_csv_import() -> None:
    st.markdown("## 📥 Bulk CSV Import")
    st.markdown("Quickly upload multiple campus notices using a structured CSV file.")

    # 1. Downloadable Template
    st.markdown("### 1. Download CSV Template")
    st.caption("Use this template to format notices correctly before uploading.")

    template_csv = (
        "title,category,description,published_date,expiry_date,priority,audience,department\n"
        "AI Innovation Challenge 2026,Events & Cultural,Join the annual AI innovation challenge open to all departments with cash prizes.,2026-11-20,2026-12-10,High,All Students,School of Computing\n"
        "Hostel Fee Installment Extension,Administrative,Last date for paying the hostel installment has been extended without late fees.,2026-11-22,2026-12-05,Critical,Hostellers & Residents,Finance & Accounts\n"
    )

    st.download_button(
        label="📄 Download Sample CSV Template",
        data=template_csv,
        file_name="notices_import_template.csv",
        mime="text/csv",
        use_container_width=False,
    )

    st.markdown("---")

    # 2. Upload Box
    st.markdown("### 2. Upload CSV File")
    uploaded_file = st.file_uploader(
        "Choose a CSV file to import:",
        type=["csv"],
        help="Upload a CSV with columns: title, category, description, published_date, expiry_date, priority, audience, department",
    )

    if uploaded_file is not None:
        if st.button("⚡ Process and Import Notices", type="primary"):
            with st.spinner("Validating rows and checking duplicates..."):
                result = dm.import_notices_from_csv(uploaded_file)

            succ = result["success_count"]
            fail = result["fail_count"]
            errors = result["errors"]
            imported = result["imported_notices"]

            if succ > 0:
                st.success(f"✅ Successfully imported **{succ}** new notices to the notice board!")

            if fail > 0:
                st.warning(f"⚠️ **{fail}** row{'s' if fail != 1 else ''} could not be imported due to validation errors.")
                st.markdown("#### 🔍 Rejection & Error Details:")
                err_df = pd.DataFrame(errors)
                st.dataframe(err_df, use_container_width=True, hide_index=True)

            if succ > 0 and imported:
                st.markdown("#### 📋 Newly Added Notices:")
                for item in imported[:5]:
                    st.markdown(render_notice_card_html(item), unsafe_allow_html=True)
                if len(imported) > 5:
                    st.info(f"...and {len(imported) - 5} more notices successfully saved.")


# ==============================================================================
# PAGE 5: EDIT & MANAGE NOTICES
# ==============================================================================
def page_edit_delete_notice() -> None:
    st.markdown("## ✏️ Edit & Manage Notices")
    st.markdown("Update existing announcements or securely remove outdated records.")

    notices = dm.get_all_notices()
    if not notices:
        st.info("No notices available to edit or delete.")
        return

    # Select a notice to manage
    notice_options = {f"{n['id']} - {n['title']} ({n['status']})": n['id'] for n in notices}
    selected_label = st.selectbox(
        "Select Notice to Manage:",
        options=list(notice_options.keys()),
        help="Search or select a notice by ID, title, or status.",
    )
    selected_id = notice_options[selected_label]
    notice = dm.get_notice_by_id(selected_id)

    if not notice:
        st.error("Selected notice could not be retrieved.")
        return

    tab_edit, tab_delete = st.tabs(["✏️ Edit Notice Details", "🗑️ Delete Notice"])

    # --- TAB 1: EDIT NOTICE ---
    with tab_edit:
        st.markdown(f"### Editing **{notice['id']}**: {notice['title']}")

        # Parse stored dates
        try:
            pub_default = datetime.strptime(notice["published_date"][:10], "%Y-%m-%d").date()
        except Exception:
            pub_default = date.today()

        try:
            exp_default = datetime.strptime(notice["expiry_date"][:10], "%Y-%m-%d").date()
        except Exception:
            exp_default = date.today() + timedelta(days=7)

        with st.form(f"edit_form_{notice['id']}"):
            new_title = st.text_input("Notice Title *", value=notice.get("title", ""))

            col1, col2 = st.columns(2)
            with col1:
                cat_idx = CATEGORIES.index(notice["category"]) if notice.get("category") in CATEGORIES else 0
                new_cat = st.selectbox(
                    "Category *",
                    CATEGORIES,
                    index=cat_idx,
                    format_func=lambda x: f"{CATEGORY_ICONS.get(x, '📌')} {x}",
                )
            with col2:
                pri_idx = PRIORITIES.index(notice["priority"]) if notice.get("priority") in PRIORITIES else 2
                new_pri = st.selectbox("Priority *", PRIORITIES, index=pri_idx)

            col3, col4 = st.columns(2)
            with col3:
                aud_idx = AUDIENCES.index(notice["audience"]) if notice.get("audience") in AUDIENCES else 0
                new_aud = st.selectbox("Target Audience *", AUDIENCES, index=aud_idx)
            with col4:
                new_dept = st.text_input("Department *", value=notice.get("department", "Administration"))

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                new_pub = st.date_input("Published Date *", value=pub_default)
            with col_d2:
                new_exp = st.date_input("Expiry Date *", value=exp_default)

            new_desc = st.text_area("Notice Description *", value=notice.get("description", ""), height=160)

            save_submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)

        if save_submitted:
            update_payload = {
                "title": new_title,
                "category": new_cat,
                "description": new_desc,
                "published_date": new_pub,
                "expiry_date": new_exp,
                "priority": new_pri,
                "audience": new_aud,
                "department": new_dept,
            }
            success, msg, updated_notice = dm.update_notice(notice["id"], update_payload)
            if success and updated_notice:
                st.success(f"✅ {msg}")
                st.markdown("#### Updated Preview:")
                st.markdown(render_notice_card_html(updated_notice), unsafe_allow_html=True)
            else:
                st.error(f"❌ Update failed: {msg}")

    # --- TAB 2: DELETE NOTICE ---
    with tab_delete:
        st.markdown(f"### Danger Zone: Delete **{notice['id']}**")
        st.warning(
            f"You are about to permanently delete **{notice['id']} - {notice['title']}**. This action cannot be undone."
        )

        st.markdown(render_notice_card_html(notice), unsafe_allow_html=True)

        confirm_check = st.checkbox(
            f"I confirm that I want to permanently delete notice {notice['id']}.",
            key=f"del_confirm_{notice['id']}",
        )

        if st.button("🗑️ Permanently Delete Notice", type="primary", disabled=not confirm_check):
            del_success, del_msg = dm.delete_notice(notice["id"])
            if del_success:
                st.success(f"🗑️ {del_msg}")
                st.info("The notice board has been updated. Please refresh or navigate to view current notices.")
            else:
                st.error(f"❌ Error deleting notice: {del_msg}")


# ==============================================================================
# PAGE 6: REPORTS & ANALYTICS
# ==============================================================================
def page_reports_analytics() -> None:
    st.markdown("## 📑 Summary Reports & Analytics")
    st.markdown("Institutional intelligence, category matrices, monthly trends, and data exports.")

    notices = dm.get_all_notices()
    metrics = dm.get_dashboard_metrics(notices)
    df = dm.get_dataframe(notices)

    # 1. High-level Summary Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Notices", metrics["total"])
    col2.metric("Active Live", metrics["active"])
    col3.metric("Upcoming Scheduled", metrics["upcoming"])
    col4.metric("Critical & High", metrics["urgent_count"])

    st.markdown("---")

    # 2. Export Buttons
    st.markdown("### 📥 Download Notice Data")
    st.markdown("Download all campus notices locally for spreadsheet analysis, institutional archiving, or backup.")

    col_csv, col_json = st.columns(2)
    with col_csv:
        csv_data = dm.export_to_csv_bytes(notices)
        st.download_button(
            label="📄 Download Notices as CSV",
            data=csv_data,
            file_name=f"college_notices_{date.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_json:
        json_data = dm.export_to_json_bytes(notices)
        st.download_button(
            label="📦 Download Notices as JSON",
            data=json_data,
            file_name=f"college_notices_{date.today().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True,
        )

    st.markdown("---")

    # 3. Category Analytics Table
    st.markdown("### 📊 Category Analytics Breakdown")
    cat_analytics = dm.get_category_analytics(notices)
    st.dataframe(cat_analytics, use_container_width=True, hide_index=True)

    # 4. Monthly Publication Trends
    st.markdown("### 📈 Monthly Publication Trend")
    monthly_stats = dm.get_monthly_statistics(notices)
    if not monthly_stats.empty:
        col_m1, col_m2 = st.columns([1.5, 1])
        with col_m1:
            render_monthly_chart(monthly_stats)
        with col_m2:
            st.dataframe(monthly_stats, use_container_width=True, hide_index=True)

    # 5. Department Summary
    st.markdown("### 🏛️ Department Activity Report")
    if not df.empty:
        dept_counts = df["department"].value_counts().reset_index()
        dept_counts.columns = ["Department / Issuing Office", "Total Notices Issued"]
        st.dataframe(dept_counts, use_container_width=True, hide_index=True)


# ==============================================================================
# PAGE 7: USER GUIDE & LOGS
# ==============================================================================
def page_guide_logs() -> None:
    st.markdown("## ℹ️ College Notice Board Organizer Guide")
    st.markdown(
        "Welcome to **CampusPulse**, a beginner-friendly notice board system designed for college campuses."
    )

    with st.expander("⏱️ How Does Automatic Status & Expiry Detection Work?", expanded=True):
        st.markdown(
            """
            The application dynamically compares each notice's **Published Date** and **Expiry Date** against today's date:
            
            1. 🟢 **Active Notice:**
               - Condition: `Published Date <= Today <= Expiry Date`
               - Meaning: The announcement is currently open, ongoing, or within its active window.
            2. 🔵 **Upcoming Notice:**
               - Condition: `Published Date > Today`
               - Meaning: The announcement is scheduled for future release. It will automatically switch to **Active** when its published date arrives!
            3. ⚪ **Expired Notice:**
               - Condition: `Expiry Date < Today`
               - Meaning: The deadline or event date has passed. It is preserved for archival records.
            """
        )

    with st.expander("🛡️ Duplicate Prevention & Input Validation", expanded=False):
        st.markdown(
            """
            - **Duplicate Detection:** Checks normalized titles against existing notices in the same category. If an identical title already exists, submission is rejected with the existing notice ID.
            - **Year Range Validation:** Dates must fall within the range 2000–2040 to prevent accidental keyboard typos.
            - **Logical Order:** Expiry date cannot be earlier than the published date.
            - **Length Minimums:** Title at least 3 characters, description at least 10 characters.
            """
        )

    with st.expander("💾 Reliability, Backups & Dual Sync", expanded=False):
        st.markdown(
            """
            - **Primary Storage:** `data/notices.json` provides fast, structured data storage.
            - **Automatic Safety Backup:** Every modification creates a backup copy at `data/notices.json.bak`.
            - **CSV Synchronization:** Every insert, update, or bulk import automatically syncs to `data/notices.csv`.
            - **Atomic Writes:** Uses temporary files during write operations to eliminate risks of corrupted files.
            """
        )

    st.markdown("---")

    # Application Audit Logs
    st.markdown("### 📜 System Activity Logs")
    st.caption("Timestamped operations log recording notice creation, updates, deletions, and CSV imports.")
    recent_logs = dm.get_recent_logs(limit=40)
    with st.expander("View Recent Activity Logs (Last 40 entries)", expanded=False):
        st.code("\n".join(recent_logs), language="log")

    st.markdown("---")
    st.markdown("### 🔄 Reset Sample Data (Demo Mode)")
    st.info("Demonstrating or grading the project? You can reset the notices back to the initial 32 college samples anytime.")

    if st.button("♻️ Reset to Default Sample Data (32 Notices)", type="secondary"):
        new_samples = dm.reset_to_sample_data()
        st.success(f"Successfully reloaded {len(new_samples)} fresh realistic sample college notices!")
        st.rerun()


# ==============================================================================
# MAIN ROUTING
# ==============================================================================
def main() -> None:
    current_page = sidebar_navigation()

    if current_page == "📊 Dashboard":
        page_dashboard()
    elif current_page == "📋 Browse & Search Notices":
        page_browse_notices()
    elif current_page == "➕ Add New Notice":
        page_add_notice()
    elif current_page == "📥 Bulk CSV Import":
        page_bulk_csv_import()
    elif current_page == "✏️ Edit & Manage Notices":
        page_edit_delete_notice()
    elif current_page == "📑 Reports & Analytics":
        page_reports_analytics()
    elif current_page == "ℹ️ User Guide & Logs":
        page_guide_logs()


if __name__ == "__main__":
    main()
