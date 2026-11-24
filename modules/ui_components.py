"""
UI Components and Theme Styling for Notice Board Organizer.
Provides custom CSS, badge generators, metric cards, notice cards, and chart helpers.
"""

from typing import Any, Dict, List, Optional
import altair as alt
import pandas as pd
import streamlit as st

from config import (
    APP_SUBTITLE,
    APP_TITLE,
    CATEGORY_COLORS,
    CATEGORY_ICONS,
    COLLEGE_NAME,
    PRIORITY_COLORS,
    STATUS_COLORS,
    STATUS_ICONS,
)


def inject_custom_css() -> None:
    """Inject polished, modern CSS styling into the Streamlit app."""
    custom_css = """
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Top Banner Styling */
    .portal-banner {
        background: linear-gradient(135deg, #1E3A8A 0%, #1D4ED8 50%, #0284C7 100%);
        color: white;
        padding: 24px 28px;
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(30, 58, 138, 0.25);
        margin-bottom: 24px;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    .portal-banner h1 {
        color: #FFFFFF !important;
        font-size: 26px !important;
        font-weight: 800 !important;
        margin: 0 0 4px 0 !important;
        letter-spacing: -0.5px;
    }
    .portal-banner p {
        color: #E0E7FF !important;
        font-size: 14px !important;
        margin: 0 !important;
        font-weight: 500;
    }

    /* Metric Cards */
    .metric-card {
        background: #FFFFFF;
        border-radius: 14px;
        padding: 18px 20px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        transition: transform 0.18s ease, box-shadow 0.18s ease;
        position: relative;
        overflow: hidden;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.07);
    }
    .metric-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
    }
    .metric-card.total::before { background: #6366F1; }
    .metric-card.active::before { background: #10B981; }
    .metric-card.expired::before { background: #94A3B8; }
    .metric-card.upcoming::before { background: #3B82F6; }
    .metric-card.critical::before { background: #DC2626; }

    .metric-title {
        font-size: 13px;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 32px;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.1;
    }
    .metric-subtext {
        font-size: 12px;
        color: #64748B;
        margin-top: 6px;
        font-weight: 500;
    }

    /* Pill Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
        line-height: 1.2;
    }
    .badge-active {
        background-color: #ECFDF5;
        color: #065F46;
        border: 1px solid #A7F3D0;
    }
    .badge-upcoming {
        background-color: #EFF6FF;
        color: #1E40AF;
        border: 1px solid #BFDBFE;
    }
    .badge-expired {
        background-color: #F1F5F9;
        color: #475569;
        border: 1px solid #CBD5E1;
    }

    /* Priority Badges */
    .badge-priority-critical {
        background-color: #7F1D1D;
        color: #FFFFFF;
        border: 1px solid #991B1B;
        font-weight: 700;
    }
    .badge-priority-high {
        background-color: #FEF2F2;
        color: #991B1B;
        border: 1px solid #FECACA;
    }
    .badge-priority-medium {
        background-color: #FFFBEB;
        color: #92400E;
        border: 1px solid #FDE68A;
    }
    .badge-priority-low {
        background-color: #EFF6FF;
        color: #1E40AF;
        border: 1px solid #BFDBFE;
    }

    .badge-warning {
        background-color: #FEF3C7;
        color: #92400E;
        border: 1px solid #F59E0B;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11.5px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    .badge-category {
        background-color: #F8FAFC;
        color: #334155;
        border: 1px solid #E2E8F0;
        font-size: 11px;
    }

    /* Notice Card in List */
    .notice-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 14px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
        transition: all 0.2s ease;
    }
    .notice-card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 6px 16px rgba(0,0,0,0.06);
    }
    .notice-card.urgent {
        border-left: 4px solid #DC2626;
        background: linear-gradient(to right, #FFFBFB, #FFFFFF);
    }
    .notice-card.upcoming-card {
        border-left: 4px solid #3B82F6;
    }
    .notice-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 8px;
        flex-wrap: wrap;
    }
    .notice-title {
        font-size: 17px;
        font-weight: 700;
        color: #1E293B;
        margin: 0;
    }
    .notice-desc {
        color: #475569;
        font-size: 14px;
        line-height: 1.55;
        margin: 10px 0 12px 0;
    }
    .notice-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 14px;
        font-size: 12px;
        color: #64748B;
        padding-top: 10px;
        border-top: 1px solid #F1F5F9;
    }
    .notice-meta-item {
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    /* Alert Banner */
    .alert-box {
        background: #FFFBEB;
        border-left: 4px solid #F59E0B;
        padding: 14px 18px;
        border-radius: 8px;
        margin-bottom: 20px;
        color: #92400E;
        font-size: 13.5px;
    }
    .alert-box.critical-alert {
        background: #FEF2F2;
        border-left: 4px solid #DC2626;
        color: #991B1B;
    }
    .alert-box strong {
        color: #78350F;
    }
    .alert-box.critical-alert strong {
        color: #7F1D1D;
    }

    /* Sidebar info card */
    .sidebar-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px;
        font-size: 12.5px;
        color: #475569;
        margin-top: 16px;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def render_portal_header() -> None:
    """Render the top college dashboard banner."""
    html = f"""
    <div class="portal-banner">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
            <div>
                <h1>🏛️ {APP_TITLE}</h1>
                <p>{APP_SUBTITLE} • {COLLEGE_NAME}</p>
            </div>
            <div style="background: rgba(255,255,255,0.18); padding: 8px 16px; border-radius: 30px; font-size: 13px; font-weight: 600; backdrop-filter: blur(4px);">
                📅 Active Academic Session 2026–2027
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_dashboard_metrics(metrics: Dict[str, Any]) -> None:
    """Render 4 prominent KPI metric cards with status indicator accents."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card total">
                <div class="metric-title">📋 Total Notices</div>
                <div class="metric-value">{metrics['total']}</div>
                <div class="metric-subtext">All campus announcements</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card active">
                <div class="metric-title">🟢 Active Notices</div>
                <div class="metric-value">{metrics['active']}</div>
                <div class="metric-subtext">Live & currently actionable</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card upcoming">
                <div class="metric-title">🔵 Upcoming Notices</div>
                <div class="metric-value">{metrics['upcoming']}</div>
                <div class="metric-subtext">Scheduled for future release</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-card expired">
                <div class="metric-title">⚪ Expired Notices</div>
                <div class="metric-value">{metrics['expired']}</div>
                <div class="metric-subtext">Concluded / archived deadlines</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_status_badge_html(status: str) -> str:
    """Return HTML string for status badge."""
    icon = STATUS_ICONS.get(status, "⚪")
    css_class = f"badge-{status.lower()}"
    return f'<span class="badge {css_class}">{icon} {status}</span>'


def render_priority_badge_html(priority: str) -> str:
    """Return HTML string for priority badge with new Critical level."""
    css_class = f"badge-priority-{priority.lower()}"
    dots = {"Critical": "🚨", "High": "🔴", "Medium": "🟡", "Low": "🔵"}.get(priority, "⚪")
    return f'<span class="badge {css_class}">{dots} {priority}</span>'


def render_category_badge_html(category: str) -> str:
    """Return HTML string for category badge."""
    icon = CATEGORY_ICONS.get(category, "📌")
    return f'<span class="badge badge-category">{icon} {category}</span>'


def render_notice_card_html(notice: Dict[str, Any]) -> str:
    """Render a clean, modern HTML card for an individual notice with urgent highlights and deadline warnings."""
    status_badge = render_status_badge_html(notice.get("status", "Active"))
    priority = notice.get("priority", "Medium")
    priority_badge = render_priority_badge_html(priority)
    category_badge = render_category_badge_html(notice.get("category", "General"))
    warning = notice.get("deadline_warning")

    warning_html = f'<div style="margin-top: 4px;"><span class="badge-warning">{warning}</span></div>' if warning else ""

    # Card class accents
    card_classes = ["notice-card"]
    if priority == "Critical" or (warning and notice.get("status") == "Active"):
        card_classes.append("urgent")
    elif notice.get("status") == "Upcoming":
        card_classes.append("upcoming-card")

    card_class_str = " ".join(card_classes)

    html = f"""
    <div class="{card_class_str}">
        <div class="notice-header">
            <div>
                <div style="margin-bottom: 6px; display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; background: #F1F5F9; color: #475569; padding: 2px 7px; border-radius: 4px; font-weight: 600;">{notice.get('id')}</span>
                    {category_badge}
                    {priority_badge}
                </div>
                <h3 class="notice-title">{notice.get('title')}</h3>
            </div>
            <div style="text-align: right; min-width: 140px;">
                {status_badge}
                {warning_html}
                <div style="font-size: 11.5px; color: #64748B; margin-top: 4px; font-weight: 500;">
                    {notice.get('time_label', '')}
                </div>
            </div>
        </div>
        <div class="notice-desc">
            {notice.get('description')}
        </div>
        <div class="notice-meta">
            <span class="notice-meta-item">📅 <strong>Published:</strong> {notice.get('published_date')}</span>
            <span class="notice-meta-item">⏳ <strong>Expires:</strong> {notice.get('expiry_date')}</span>
            <span class="notice-meta-item">👥 <strong>Audience:</strong> {notice.get('audience', 'All Students')}</span>
            <span class="notice-meta-item">🏛️ <strong>Dept:</strong> {notice.get('department', 'Administration')}</span>
        </div>
    </div>
    """
    return html


def render_category_chart(notices: List[Dict[str, Any]]) -> None:
    """Render an Altair bar chart displaying category distribution."""
    if not notices:
        st.info("No notices available to plot category chart.")
        return

    df = pd.DataFrame(notices)
    cat_counts = df["category"].value_counts().reset_index()
    cat_counts.columns = ["Category", "Notices"]

    chart = (
        alt.Chart(cat_counts)
        .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6)
        .encode(
            x=alt.X("Notices:Q", title="Number of Notices"),
            y=alt.Y("Category:N", sort="-x", title=None),
            color=alt.Color("Category:N", legend=None, scale=alt.Scale(scheme="tableau10")),
            tooltip=["Category", "Notices"],
        )
        .properties(height=280)
        .configure_axis(grid=False)
    )

    st.altair_chart(chart, use_container_width=True)


def render_status_chart(notices: List[Dict[str, Any]]) -> None:
    """Render a donut chart for status distribution."""
    if not notices:
        return

    df = pd.DataFrame(notices)
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]

    color_scale = alt.Scale(
        domain=["Active", "Upcoming", "Expired"],
        range=["#10B981", "#3B82F6", "#94A3B8"],
    )

    chart = (
        alt.Chart(status_counts)
        .mark_arc(innerRadius=45, stroke="#fff")
        .encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(field="Status", type="nominal", scale=color_scale, title="Status"),
            tooltip=["Status", "Count"],
        )
        .properties(height=280)
    )

    st.altair_chart(chart, use_container_width=True)


def render_monthly_chart(monthly_df: pd.DataFrame) -> None:
    """Render a monthly timeline chart of notice publication trends."""
    if monthly_df.empty:
        st.info("No monthly timeline data available.")
        return

    chart = (
        alt.Chart(monthly_df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("Month:N", title="Month (YYYY-MM)", sort=None),
            y=alt.Y("Total Published:Q", title="Announcements Published"),
            color=alt.value("#2563EB"),
            tooltip=["Month", "Total Published", "Active", "Upcoming", "Expired"],
        )
        .properties(height=260)
    )

    st.altair_chart(chart, use_container_width=True)
