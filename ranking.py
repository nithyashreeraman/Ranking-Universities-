import streamlit as st
import pandas as pd
import plotly.express as px
import re
import plotly.graph_objects as go

# --- Page Setup ---
st.set_page_config(page_title="University Dashboard", layout="wide")
st.title("🏛️ University Rankings Dashboard")

# --- Cache Data Loading ---
@st.cache_data
def load_data():
    times_df = pd.read_excel("TIMES.xlsx", sheet_name="Sheet1")
    qs_df = pd.read_excel("QS.xlsx", sheet_name="Sheet1")
    usn_df = pd.read_excel("USN.xlsx", sheet_name="Sheet1")
    washington_df = pd.read_excel("Washington.xlsx", sheet_name="Sheet1")
    return times_df, qs_df, usn_df, washington_df

# --- Cache Common Universities ---
@st.cache_data
def get_common_universities(times_df, qs_df, usn_df, washington_df):
    return set(times_df["IPEDS_Name"]) & set(qs_df["IPEDS_Name"]) & set(usn_df["IPEDS_Name"]) & set(washington_df["IPEDS_Name"])

# --- Cache Combined Filtered Dataset ---
@st.cache_data
def get_filtered_combined_df(_combined_df, common_universities, nj_filter):
    combined_common_df = _combined_df[_combined_df["IPEDS_Name"].isin(common_universities)]
    if nj_filter == "Yes":
        combined_common_df = combined_common_df[combined_common_df["New_Jersey_University"] == "Yes"]
    elif nj_filter == "No":
        combined_common_df = combined_common_df[combined_common_df["New_Jersey_University"] == "No"]
    return combined_common_df

# --- Load Data ---
times_df, qs_df, usn_df, washington_df = load_data()

# --- Common Data Preparation ---
for df in [times_df, qs_df, usn_df, washington_df]:
    df["Year"] = df["Year"].astype(int)
    df["IPEDS_Name"] = df["IPEDS_Name"].astype(str)

NJIT_NAME = "New Jersey Institute of Technology"

# --- Identify Common Universities ---
common_universities = get_common_universities(times_df, qs_df, usn_df, washington_df)

# --- Sidebar Filters ---
st.sidebar.header("🔍 Filters")

years = sorted(
    list(
        set(times_df["Year"].unique()) |
        set(qs_df["Year"].unique()) |
        set(usn_df["Year"].unique()) |
        set(washington_df["Year"].unique())
    )
)
selected_years = st.sidebar.multiselect("Select Years", years, default=years)

nj_filter = st.sidebar.selectbox("Include Only NJ Universities?", ["All", "Yes", "No"])

# --- Build Full Base Dataset from All Agencies ---
combined_df = pd.concat([times_df, qs_df, usn_df, washington_df], ignore_index=True)

# --- Filter Combined Dataset ---
combined_common_df = get_filtered_combined_df(combined_df, common_universities, nj_filter)

# --- Final Available Universities for Dropdown ---
common_universities_filtered = sorted([u for u in combined_common_df["IPEDS_Name"].unique() if u != NJIT_NAME])

# --- Global Selection ---
global_selected_uni = st.sidebar.selectbox("Compare NJIT with:", common_universities_filtered)

# --- Find Extra Universities Per Agency ---
extra_times_unis = sorted([u for u in times_df["IPEDS_Name"].unique() if (u not in common_universities and u != NJIT_NAME)])
extra_qs_unis = sorted([u for u in qs_df["IPEDS_Name"].unique() if (u not in common_universities and u != NJIT_NAME)])
extra_usn_unis = sorted([u for u in usn_df["IPEDS_Name"].unique() if (u not in common_universities and u != NJIT_NAME)])
extra_washington_unis = sorted([u for u in washington_df["IPEDS_Name"].unique() if (u not in common_universities and u != NJIT_NAME)])

# --- Filter Datasets Globally ---
times_filtered = times_df[
    (times_df["Year"].isin(selected_years)) &
    (times_df["IPEDS_Name"].isin([NJIT_NAME, global_selected_uni]))
]

qs_filtered = qs_df[
    (qs_df["Year"].isin(selected_years)) &
    (qs_df["IPEDS_Name"].isin([NJIT_NAME, global_selected_uni]))
]

usn_filtered = usn_df[
    (usn_df["Year"].isin(selected_years)) &
    (usn_df["IPEDS_Name"].isin([NJIT_NAME, global_selected_uni]))
]

washington_filtered = washington_df[
    (washington_df["Year"].isin(selected_years)) &
    (washington_df["IPEDS_Name"].isin([NJIT_NAME, global_selected_uni]))
]

# --- Helper Function for KPIs ---
def get_metric_value(df, university, column):
    try:
        val = df[df["IPEDS_Name"] == university][column].values[0]
        return val if pd.notna(val) else "N/A"
    except:
        return "N/A"

# --- Setup Tabs ---
tabs = st.tabs(["📊 Overview", "🟣 TIMES", "🟨 QS", "📘 USN", "🔵 Washington Monthly"])

# Shared Chart Function for All Tabs
def plot_chart_sorted(df, metric_col, title_label, description, color_map, comparison_unis, height=400):
    df = df.copy()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df = df.sort_values("Year")
    df["Year"] = df["Year"].astype(str)

    fig = px.line(
        df,
        x="Year",
        y=metric_col,
        text=metric_col,
        color="IPEDS_Name",
        markers=True,
        color_discrete_map=color_map,
        title=title_label
    )
    fig.update_traces(
        textposition="top center",
        texttemplate="%{text:.2f}",
        textfont_size=10,
        connectgaps=True
    )
    fig.update_layout(
        height=height,
        margin=dict(t=30, b=70, l=30, r=30),
        title_font=dict(size=15, color="#333"),
        title_x=0.0,
        xaxis=dict(type='category'),
        xaxis_title="Year",
        yaxis_title=title_label,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.35,
            xanchor="center",
            x=0.5,
            font=dict(size=9),
            bgcolor='rgba(0,0,0,0)',
            title_text=None
        )
    )
    st.plotly_chart(fig, use_container_width=True)

    # Chart Description Below
    st.markdown(f"""
        <div style='text-align:center; font-size:0.85rem; font-weight:bold; color:#555; margin-top:8px; margin-bottom:20px;'>
            {description}
        </div>
    """, unsafe_allow_html=True)

# --- Global KPI Box Styling ---
st.markdown("""
    <style>
    .kpi-box {
        background-color: #F6F6F6;
        padding: 10px 8px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0px 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        min-height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .kpi-box h4 {
        font-size: 0.78rem;
        margin-bottom: 6px;
        color: #333;
    }
    .kpi-box .value {
        font-size: 0.9rem;
        font-weight: 600;
        color: #E10600;
        margin-bottom: 4px;
    }
    .kpi-box .value-alt {
        font-size: 0.9rem;
        font-weight: 600;
        color: #1F77B4;
    }
    </style>
""", unsafe_allow_html=True)

with tabs[0]:
    st.markdown("""
        <h2 style='text-align: center; color: #4B4B4B;'>Overall Ranking</h2>
    """, unsafe_allow_html=True)

    latest_years = {
        "TIMES": max(times_filtered["Year"].unique(), default=None),
        "QS": max(qs_filtered["Year"].unique(), default=None),
        "USN": max(usn_filtered["Year"].unique(), default=None),
        "Washington": max(washington_filtered["Year"].unique(), default=None)
    }

    overview_kpi_metrics = {
        "Times_Rank": ("TIMES Rank", times_filtered, "TIMES"),
        "QS_Rank": ("QS Rank", qs_filtered, "QS"),
        "Rank": ("USN Rank", usn_filtered, "USN"),
        "Washington_Rank": ("Washington Rank", washington_filtered, "Washington")
    }

    kpi_data = []
    for metric, (label, df, agency) in overview_kpi_metrics.items():
        year = latest_years[agency]
        njit_val = get_metric_value(df[df["Year"] == year], NJIT_NAME, metric)
        other_val = get_metric_value(df[df["Year"] == year], global_selected_uni, metric)
        kpi_data.append((f"{label} ({year})", njit_val, other_val))

    kpi_cols = st.columns(4)
    for idx, (label, njit_val, other_val) in enumerate(kpi_data):
        with kpi_cols[idx]:
            st.markdown(
                f"<div class='kpi-box'>"
                f"<h4>{label}</h4>"
                f"<div class='value'>NJIT: {njit_val}</div>"
                f"<div class='value-alt'>{global_selected_uni}: {other_val}</div>"
                f"</div>", 
                unsafe_allow_html=True
            )

    st.divider()

    # --- TIMES Rank Chart (Range Parsing) ---
    def parse_rank_range(rank_str):
        try:
            parts = rank_str.replace("–", "-").split("-")
            if len(parts) == 2:
                return (int(parts[0]), int(parts[1]), (int(parts[0]) + int(parts[1])) // 2)
            else:
                val = int(rank_str)
                return (val, val, val)
        except:
            return (None, None, None)

    def build_rank_range_df(df, metric_col):
        df = df.copy()
        df = df[df[metric_col].notna()]
        df[["low", "high", "mid"]] = df[metric_col].apply(lambda r: pd.Series(parse_rank_range(str(r))))
        return df[df["mid"].notna()]

    metrics_tabs = st.tabs(["TIMES Rank", "QS Rank", "USN Rank", "Washington Monthly Rank"])

    with metrics_tabs[0]:
        times_ranks = build_rank_range_df(times_filtered, "Times_Rank")
        fig = px.line(
            times_ranks.sort_values("Year"),
            x="Year",
            y="mid",
            error_y=times_ranks["high"] - times_ranks["mid"],
            error_y_minus=times_ranks["mid"] - times_ranks["low"],
            color="IPEDS_Name",
            markers=True,
            text=times_ranks["Times_Rank"],
            color_discrete_map={NJIT_NAME: "#E10600", global_selected_uni: "#1F77B4"},
            title="TIMES Rank"
        )
        fig.update_traces(textposition="top center", textfont_size=10)
        fig.update_layout(
            height=450,
            margin=dict(t=30, b=30, l=30, r=30),
            title_font=dict(size=15),
            title_x=0.0,
            xaxis=dict(type='category'),
            yaxis_title="Rank",
            yaxis_autorange="reversed",
            legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("<div style='text-align:center; font-size:0.85rem; margin-top:-5px;'>TIMES ranking is displayed as a range (e.g., 501–600). Midpoints are used for plotting, but labels show the full range</div>", unsafe_allow_html=True)

    with metrics_tabs[1]:
        qs_ranks = build_rank_range_df(qs_filtered, "QS_Rank")
        fig = px.line(
            qs_ranks.sort_values("Year"),
            x="Year",
            y="mid",
            error_y=qs_ranks["high"] - qs_ranks["mid"],
            error_y_minus=qs_ranks["mid"] - qs_ranks["low"],
            color="IPEDS_Name",
            markers=True,
            text=qs_ranks["QS_Rank"],
            color_discrete_map={NJIT_NAME: "#E10600", global_selected_uni: "#1F77B4"},
            title="QS Rank"
        )
        fig.update_traces(textposition="top center", textfont_size=10)
        fig.update_layout(
            height=450,
            margin=dict(t=30, b=30, l=30, r=30),
            title_font=dict(size=15),
            title_x=0.0,
            xaxis=dict(type='category'),
            yaxis_title="Rank",
            yaxis_autorange="reversed",
            legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("<div style='text-align:center; font-size:0.85rem; margin-top:-5px;'>QS rankings are shown as ranges. Midpoints are used for comparison, but original range is labeled</div>", unsafe_allow_html=True)

    with metrics_tabs[2]:
        fig = px.line(
            usn_filtered.sort_values("Year"),
            x="Year",
            y="Rank",
            color="IPEDS_Name",
            markers=True,
            text="Rank",
            color_discrete_map={NJIT_NAME: "#E10600", global_selected_uni: "#1F77B4"},
            title="USN Rank"
        )
        fig.update_traces(textposition="top center", texttemplate="%{text}")
        fig.update_layout(
            height=450,
            margin=dict(t=30, b=30, l=30, r=30),
            title_font=dict(size=15),
            title_x=0.0,
            xaxis=dict(type='category'),
            yaxis_title="Rank",
            yaxis_autorange="reversed",
            legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("<div style='text-align:center; font-size:0.85rem; margin-top:-5px;'>USN ranking is displayed directly. Lower rank indicates better performance</div>", unsafe_allow_html=True)

    with metrics_tabs[3]:
        fig = px.line(
            washington_filtered.sort_values("Year"),
            x="Year",
            y="Washington_Rank",
            color="IPEDS_Name",
            markers=True,
            text="Washington_Rank",
            color_discrete_map={NJIT_NAME: "#E10600", global_selected_uni: "#1F77B4"},
            title="Washington Monthly Rank"
        )
        fig.update_traces(textposition="top center", texttemplate="%{text}")
        fig.update_layout(
            height=450,
            margin=dict(t=30, b=30, l=30, r=30),
            title_font=dict(size=15),
            title_x=0.0,
            xaxis=dict(type='category'),
            yaxis_title="Rank",
            yaxis_autorange="reversed",
            legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("<div style='text-align:center; font-size:0.85rem; margin-top:-5px;'>Washington Monthly rankings are plotted yearly. Lower ranks indicate stronger outcomes</div>", unsafe_allow_html=True)

with tabs[1]:
    st.markdown("<h2 style='text-align: center; color: #4B4B4B;'>TIMES Ranking</h2>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='dropdown-corner'>", unsafe_allow_html=True)
        times_selected_uni = st.selectbox(
            "🔎 Select a different University for TIMES:",
            options=["Global Selected University"] + extra_times_unis,
            index=0,
            key="times_optional_uni",
            label_visibility="collapsed"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    final_times_uni = global_selected_uni if times_selected_uni == "Global Selected University" else times_selected_uni
    color_map = {NJIT_NAME: "#E10600", final_times_uni: "#1F77B4"}
    comparison_unis = [NJIT_NAME, final_times_uni]

    times_filtered = times_df[
        (times_df["Year"].isin(selected_years)) &
        (times_df["IPEDS_Name"].isin(comparison_unis))
    ]

    latest_times_year = max([y for y in selected_years if y in times_filtered["Year"].unique()], default=None)
    kpi_row = times_filtered[times_filtered["Year"] == latest_times_year]

    kpi_metrics = {
        "Times_Rank": "🏅 Rank",
        "Overall": "📊 Overall Score",
        "Teaching": "📖 Teaching",
        "Research_Quality": "🔬 Research Quality",
        "Research_Environment": "🏛️ Research Environment",
        "International_Students": "🌍 Intl. Students %",
        "No_of_students_per_staff": "👩‍🏫 Student/Staff Ratio",
        "No_of_FTE_Students": "🎓 FTE Students"
    }

    kpi_keys = list(kpi_metrics.keys())
    for i in range(0, len(kpi_keys), 4):
        row = st.columns(4)
        for j in range(4):
            if i + j < len(kpi_keys):
                col_key = kpi_keys[i + j]
                label = kpi_metrics[col_key] + f" ({latest_times_year})"
                njit_val = get_metric_value(kpi_row, NJIT_NAME, col_key)
                other_val = get_metric_value(kpi_row, final_times_uni, col_key)
                row[j].markdown(
                    f"<div class='kpi-box'><h4>{label}</h4>"
                    f"<div class='value'>NJIT: {njit_val}</div>"
                    f"<div class='value-alt'>{final_times_uni}: {other_val}</div></div>",
                    unsafe_allow_html=True
                )

    section = st.radio(
        "Choose TIMES Section",
        ["📖 Teaching", "🔬 Research Performance", "🌍 Global Engagement & Gender"],
        horizontal=True
    )

    if section == "📖 Teaching":
        teaching_data = times_filtered[["Year", "IPEDS_Name", "Teaching"]]
        plot_chart_sorted(
            df=teaching_data,
            metric_col="Teaching",
            title_label="📖 Teaching (29.5%)",
            description="Quality of learning environment via teaching reputation and staff ratios",
            color_map=color_map,
            comparison_unis=comparison_unis
        )

    elif section == "🔬 Research Performance":
        col1, col2 = st.columns(2)
        with col1:
            rq_data = times_filtered[["Year", "IPEDS_Name", "Research_Quality"]]
            plot_chart_sorted(
                df=rq_data,
                metric_col="Research_Quality",
                title_label="🔬 Research Quality (30%)",
                description="Research excellence through citation impact and scholarly influence",
                color_map=color_map,
                comparison_unis=comparison_unis
            )
        with col2:
            re_data = times_filtered[["Year", "IPEDS_Name", "Research_Environment"]]
            plot_chart_sorted(
                df=re_data,
                metric_col="Research_Environment",
                title_label="🏛️ Research Environment (29%)",
                description="Research funding, reputation, and output volume",
                color_map=color_map,
                comparison_unis=comparison_unis
            )

    elif section == "🌍 Global Engagement & Gender":
        col1, col2 = st.columns(2)
        with col1:
            intl_data = times_filtered[["Year", "IPEDS_Name", "International_Outlook"]]
            plot_chart_sorted(
                df=intl_data,
                metric_col="International_Outlook",
                title_label="🌍 International Outlook (7.5%)",
                description="Global faculty, international students, and collaboration strength",
                color_map=color_map,
                comparison_unis=comparison_unis
            )
        with col2:
            industry_data = times_filtered[["Year", "IPEDS_Name", "Industry"]]
            plot_chart_sorted(
                df=industry_data,
                metric_col="Industry",
                title_label="🏢 Industry Income (4%)",
                description="Ability to attract industry-sponsored research income",
                color_map=color_map,
                comparison_unis=comparison_unis
            )

        gender_data = times_filtered[["Year", "IPEDS_Name", "Male_Ratio", "Female_Ratio"]]
        gender_melted = gender_data.melt(
            id_vars=["Year", "IPEDS_Name"],
            value_vars=["Male_Ratio", "Female_Ratio"],
            var_name="Gender",
            value_name="Percentage"
        )
        gender_melted["Year"] = gender_melted["Year"].astype(str)

        fig = px.bar(
            gender_melted,
            x="Year",
            y="Percentage",
            color="Gender",
            barmode="group",
            facet_col="IPEDS_Name",
            color_discrete_map={
                "Male_Ratio": "#E10600",
                "Female_Ratio": "#1F77B4"
            },
            text="Percentage",
            title="👥 Gender Distribution"
        )
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1] if "=" in a.text else ""))
        fig.update_traces(textposition="inside", insidetextanchor="middle", textfont_size=10)
        fig.update_layout(
            height=450,
            margin=dict(t=30, b=20, l=30, r=30),
            title_font=dict(size=15, color="#333"),
            title_x=0.0,
            xaxis_title="Year",
            yaxis_title="Percentage",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.35,
                xanchor="center",
                x=0.5,
                font=dict(size=9),
                bgcolor='rgba(0,0,0,0)',
                title_text=None
            )
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
            <div style='text-align:center; font-size:0.85rem; font-weight:bold; color:#555; margin-top:4px; margin-bottom:8px;'>
                Gender distribution across male and female student ratios per year
            </div>
        """, unsafe_allow_html=True)

with tabs[2]:
    st.markdown("<h2 style='text-align: center; color: #4B4B4B;'>QS Ranking</h2>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='dropdown-corner'>", unsafe_allow_html=True)
        qs_selected_uni = st.selectbox(
            "🔎 Select a Different University for QS:",
            options=["Global Selected University"] + extra_qs_unis,
            index=0,
            key="qs_optional_uni",
            label_visibility="collapsed"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    final_qs_uni = global_selected_uni if qs_selected_uni == "Global Selected University" else qs_selected_uni
    color_map = {NJIT_NAME: "#E10600", final_qs_uni: "#1F77B4"}
    comparison_unis = [NJIT_NAME, final_qs_uni]

    qs_filtered = qs_df[
        (qs_df["Year"].isin(selected_years)) &
        (qs_df["IPEDS_Name"].isin(comparison_unis))
    ]

    latest_qs_year = max([y for y in selected_years if y in qs_filtered["Year"].unique()], default=None)
    kpi_row = qs_filtered[qs_filtered["Year"] == latest_qs_year]

    kpi_metrics = {
        "QS_Rank": "🏅 QS Rank",
        "Overall_Score": "📊 Overall Score",
        "Academic_Reputation": "🎓 Academic Reputation",
        "Employer_Reputation": "🏢 Employer Reputation",
        "Citations_per_Faculty": "📖 Citations/Faculty",
        "Faculty_Student_Ratio": "👩‍🏫 Faculty-Student Ratio",
        "Employment_Outcomes": "💼 Employment Outcomes",
        "Sustainability_Score": "🌱 Sustainability Score"
    }

    kpi_keys = list(kpi_metrics.keys())
    for i in range(0, len(kpi_keys), 4):
        row = st.columns(4)
        for j in range(4):
            if i + j < len(kpi_keys):
                col_key = kpi_keys[i + j]
                label = kpi_metrics[col_key] + f" ({latest_qs_year})"
                njit_val = get_metric_value(kpi_row, NJIT_NAME, col_key)
                other_val = get_metric_value(kpi_row, final_qs_uni, col_key)
                row[j].markdown(
                    f"<div class='kpi-box'><h4>{label}</h4>"
                    f"<div class='value'>NJIT: {njit_val}</div>"
                    f"<div class='value-alt'>{final_qs_uni}: {other_val}</div></div>",
                    unsafe_allow_html=True
                )

    chart_selection = st.radio(
        "Choose QS Section",
        ["🎓 Research & Learning", "🌍 Global Engagement"],
        horizontal=True
    )

    if chart_selection.startswith("🎓"):
        col1, col2 = st.columns(2)
        with col1:
            ar_data = qs_filtered[["Year", "IPEDS_Name", "Academic_Reputation"]]
            plot_chart_sorted(
                df=ar_data,
                metric_col="Academic_Reputation",
                title_label="🎓 Academic Reputation (30%)",
                description="Global survey of academic prestige.",
                color_map=color_map,
                comparison_unis=comparison_unis
            )
        with col2:
            citations_data = qs_filtered[["Year", "IPEDS_Name", "Citations_per_Faculty"]]
            plot_chart_sorted(
                df=citations_data,
                metric_col="Citations_per_Faculty",
                title_label="📖 Citations per Faculty (20%)",
                description="Research strength via faculty citation rates",
                color_map=color_map,
                comparison_unis=comparison_unis
            )

    elif chart_selection.startswith("🌍"):
        col1, col2 = st.columns(2)
        with col1:
            intl_student_data = qs_filtered[["Year", "IPEDS_Name", "International_Student_Ratio"]]
            plot_chart_sorted(
                df=intl_student_data,
                metric_col="International_Student_Ratio",
                title_label="🌎 International Student Ratio (5%)",
                description="Global student diversity at the institution",
                color_map=color_map,
                comparison_unis=comparison_unis
            )
        with col2:
            intl_faculty_data = qs_filtered[["Year", "IPEDS_Name", "International_Faculty_Ratio"]]
            plot_chart_sorted(
                df=intl_faculty_data,
                metric_col="International_Faculty_Ratio",
                title_label="👩‍🏫 International Faculty Ratio (5%)",
                description="International diversity of faculty members",
                color_map=color_map,
                comparison_unis=comparison_unis
            )

with tabs[3]:
    st.markdown("<h2 style='text-align: center; color: #4B4B4B;'>USN Ranking</h2>", unsafe_allow_html=True)

    usn_selected_uni = st.selectbox(
        "", options=["Global Selected University"] + extra_usn_unis,
        index=0, key="usn_optional_uni", label_visibility="collapsed"
    )
    final_usn_uni = global_selected_uni if usn_selected_uni == "Global Selected University" else usn_selected_uni
    color_map = {NJIT_NAME: "#E10600", final_usn_uni: "#1F77B4"}
    comparison_unis = [NJIT_NAME, final_usn_uni]

    usn_filtered_tab = usn_df[
        (usn_df["Year"].isin(selected_years)) &
        (usn_df["IPEDS_Name"].isin(comparison_unis))
    ]
    
    latest_usn_year = max([y for y in selected_years if y in usn_filtered_tab["Year"].unique()], default=None)
    kpi_row = usn_filtered_tab[usn_filtered_tab["Year"] == latest_usn_year]

    kpi_metrics = {
        "Rank": "🏅 USN Rank",
        "Peer assessment score": "🤝 Peer Assessment",
        "Actual graduation rate": "🎓 Graduation Rate",
        "Average first year retention rate": "📚 First-Year Retention",
        "Faculty resources rank": "🏫 Faculty Resources Rank",
        "Financial resources rank": "💰 Financial Resources Rank",
        "Pell Graduation Rate": "🎓 Pell Grad Rate",
        "College grad income benefit (%)": "💼 Income Benefit"
    }

    for i in range(0, len(kpi_metrics), 4):
        row = st.columns(4)
        for j in range(4):
            if i + j < len(kpi_metrics):
                col_key = list(kpi_metrics.keys())[i + j]
                label = kpi_metrics[col_key] + f" ({latest_usn_year})"
                njit_val = get_metric_value(kpi_row, NJIT_NAME, col_key)
                other_val = get_metric_value(kpi_row, final_usn_uni, col_key)
                row[j].markdown(
                    f"<div class='kpi-box'><h4>{label}</h4>"
                    f"<div class='value'>NJIT: {njit_val}</div>"
                    f"<div class='value-alt'>{final_usn_uni}: {other_val}</div></div>",
                    unsafe_allow_html=True
                )

    chart_selection = st.radio(
        "Choose USN Section",
        ["🎓 Student Success", "👩‍🏫 Faculty & Financials", "🎯 Admissions & Selectivity", "🎓 Alumni Outcomes"],
        horizontal=True
    )

    if chart_selection == "🎓 Student Success":
        col1, col2 = st.columns(2)
        with col1:
            plot_chart_sorted(
                df=usn_filtered_tab[["Year", "IPEDS_Name", "Graduation and retention rank"]],
                metric_col="Graduation and retention rank",
                title_label="🎯 Graduation & Retention Rank (20%)",
                description="Combined ranking on student graduation and retention success.",
                color_map=color_map, comparison_unis=comparison_unis
            )
        with col2:
            plot_chart_sorted(
                df=usn_filtered_tab[["Year", "IPEDS_Name", "Pell Graduation Rate"]],
                metric_col="Pell Graduation Rate",
                title_label="🎓 Pell Graduation Rate (20%)",
                description="Graduation rate of low-income Pell Grant students.",
                color_map=color_map, comparison_unis=comparison_unis
            )

    elif chart_selection == "👩‍🏫 Faculty & Financials":
        col1, col2 = st.columns(2)
        with col1:
            plot_chart_sorted(
                df=usn_filtered_tab[["Year", "IPEDS_Name", "Percent of full-time faculty"]],
                metric_col="Percent of full-time faculty",
                title_label="👩‍🏫 % Full-Time Faculty (7%)",
                description="Ratio of full-time instructional faculty.",
                color_map=color_map, comparison_unis=comparison_unis
            )
        with col2:
            plot_chart_sorted(
                df=usn_filtered_tab[["Year", "IPEDS_Name", "Faculty resources rank"]],
                metric_col="Faculty resources rank",
                title_label="🏛️ Faculty Resources Rank (7%)",
                description="Ranking based on class size, salary, and staff ratios.",
                color_map=color_map, comparison_unis=comparison_unis
            )

    elif chart_selection == "🎯 Admissions & Selectivity":
        col1, col2 = st.columns(2)
        with col1:
            plot_chart_sorted(
                df=usn_filtered_tab[["Year", "IPEDS_Name", "Top 10% of HS Class"]],
                metric_col="Top 10% of HS Class",
                title_label="📘 Top 10% HS Class (5%)",
                description="Percentage of students in top decile of their class.",
                color_map=color_map, comparison_unis=comparison_unis
            )
        with col2:
            plot_chart_sorted(
                df=usn_filtered_tab[["Year", "IPEDS_Name", "% students submitting SAT scores"]],
                metric_col="% students submitting SAT scores",
                title_label="📝 % Submitted SAT (3%)",
                description="SAT submission ratio indicating selectivity.",
                color_map=color_map, comparison_unis=comparison_unis
            )

    elif chart_selection == "🎓 Alumni Outcomes":
        plot_chart_sorted(
            df=usn_filtered_tab[["Year", "IPEDS_Name", "Alumni Giving"]],
            metric_col="Alumni Giving",
            title_label="🎓 Alumni Giving Rate (3%)",
            description="Measures alumni engagement through donations.",
            color_map=color_map, comparison_unis=comparison_unis
        )

with tabs[4]:
    st.markdown("""
        <h2 style='text-align: center; color: #4B4B4B;'>Washington Monthly Ranking</h2>
    """, unsafe_allow_html=True)

    washington_selected_uni = st.selectbox(
        "Choose Washington Monthly university:",
        options=["Global Selected University"] + extra_washington_unis,
        index=0,
        key="washington_optional_uni",
        label_visibility="collapsed"
    )
    final_washington_uni = global_selected_uni if washington_selected_uni == "Global Selected University" else washington_selected_uni
    color_map = {NJIT_NAME: "#E10600", final_washington_uni: "#1F77B4"}
    comparison_unis = [NJIT_NAME, final_washington_uni]

    washington_filtered_tab = washington_df[
        (washington_df["Year"].isin(selected_years)) &
        (washington_df["IPEDS_Name"].isin(comparison_unis))
    ]

    latest_wash_year = max([y for y in selected_years if y in washington_filtered_tab["Year"].unique()], default=None)
    kpi_row = washington_filtered_tab[washington_filtered_tab["Year"] == latest_wash_year]

    kpi_metrics = {
        "Washington_Rank": "🏅 Washington Rank",
        "8-year_graduation_rate": "🎓 8-Year Graduation Rate",
        "Pell/non-Pell_graduation_gap": "📚 Pell vs Non-Pell Grad Gap",
        "Net_price_of_attendance_for_families_below_$75,000_income": "💸 Net Price <$75k",
        "Earnings_9_years_after_college_entry": "💼 Earnings 9 Years Post-Entry",
        "Research_expenditures_in_millions": "🔬 Research Expenses (M$)",
        "Science_&_engineering_PhDs_awarded": "🎓 S&E PhDs Awarded",
        "Faculty_receiving_significant_awards": "🏆 Faculty Awards",
    }

    kpi_keys = list(kpi_metrics.keys())
    for i in range(0, len(kpi_keys), 4):
        row = st.columns(4)
        for j in range(4):
            if i + j < len(kpi_keys):
                col_key = kpi_keys[i + j]
                label = kpi_metrics[col_key] + f" ({latest_wash_year})"
                njit_val = get_metric_value(kpi_row, NJIT_NAME, col_key)
                other_val = get_metric_value(kpi_row, final_washington_uni, col_key)
                row[j].markdown(
                    f"<div class='kpi-box'><h4>{label}</h4>"
                    f"<div class='value'>NJIT: {njit_val}</div>"
                    f"<div class='value-alt'>{final_washington_uni}: {other_val}</div></div>",
                    unsafe_allow_html=True
                )

    chart_selection = st.radio(
        "Choose Washington Monthly Section",
        ["📊 Social Mobility", "🔬 Research", "🤝 Service"],
        horizontal=True
    )

    if chart_selection == "📊 Social Mobility":
        col1, col2 = st.columns(2)
        with col1:
            plot_chart_sorted(
                df=washington_filtered_tab[["Year", "IPEDS_Name", "8-year_graduation_rate"]],
                metric_col="8-year_graduation_rate",
                title_label="🎓 8-Year Graduation Rate (~6.67%)",
                description="Percentage of students graduating within 8 years",
                color_map=color_map,
                comparison_unis=comparison_unis
            )
        with col2:
            plot_chart_sorted(
                df=washington_filtered_tab[["Year", "IPEDS_Name", "Pell/non-Pell_graduation_gap"]],
                metric_col="Pell/non-Pell_graduation_gap",
                title_label="📚 Pell vs Non-Pell Grad Gap (~6.67%)",
                description="Gap in graduation rates between Pell and non-Pell students",
                color_map=color_map,
                comparison_unis=comparison_unis
            )
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            plot_chart_sorted(
                df=washington_filtered_tab[["Year", "IPEDS_Name", "Actual_vs_predicted_Pell_enrollment"]],
                metric_col="Actual_vs_predicted_Pell_enrollment",
                title_label="📈 Pell Enrollment Performance (~3.33%)",
                description="Difference between actual and predicted Pell student enrollment",
                color_map=color_map,
                comparison_unis=comparison_unis
            )
        with col2:
            plot_chart_sorted(
                df=washington_filtered_tab[["Year", "IPEDS_Name", "Net_price_of_attendance_for_families_below_$75,000_income"]],
                metric_col="Net_price_of_attendance_for_families_below_$75,000_income",
                title_label="💸 Net Price for <$75k Income (~6.67%)",
                description="Average net price for low-income families",
                color_map=color_map,
                comparison_unis=comparison_unis
            )

    elif chart_selection == "🔬 Research":
        col1, col2 = st.columns(2)
        with col1:
            plot_chart_sorted(
                df=washington_filtered_tab[["Year", "IPEDS_Name", "Research_expenditures_in_millions"]],
                metric_col="Research_expenditures_in_millions",
                title_label="🔬 Research Expenditures (M$) (~6.67%)",
                description="Total institutional research spending in millions",
                color_map=color_map,
                comparison_unis=comparison_unis
            )
        with col2:
            plot_chart_sorted(
                df=washington_filtered_tab[["Year", "IPEDS_Name", "Science_&_engineering_PhDs_awarded"]],
                metric_col="Science_&_engineering_PhDs_awarded",
                title_label="🎓 S&E PhDs Awarded (~6.67%)",
                description="Number of science and engineering PhDs awarded",
                color_map=color_map,
                comparison_unis=comparison_unis
            )
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            plot_chart_sorted(
                df=washington_filtered_tab[["Year", "IPEDS_Name", "Bachelor's_to_PhD_rank"]],
                metric_col="Bachelor's_to_PhD_rank",
                title_label="🎓 Alumni Earning PhDs (~6.67%)",
                description="Rank of undergraduate alumni earning PhDs relative to size",
                color_map=color_map,
                comparison_unis=comparison_unis
            )
        with col2:
            plot_chart_sorted(
                df=washington_filtered_tab[["Year", "IPEDS_Name", "Faculty_receiving_significant_awards"]],
                metric_col="Faculty_receiving_significant_awards",
                title_label="🏆 Faculty Awards (~6.67%)",
                description="Number of faculty receiving prestigious awards",
                color_map=color_map,
                comparison_unis=comparison_unis
            )

    elif chart_selection == "🤝 Service":
        col1, col2 = st.columns(2)
        with col1:
            plot_chart_sorted(
                df=washington_filtered_tab[["Year", "IPEDS_Name", "%_of_federal_work_study_funds_spent_on_service"]],
                metric_col="%_of_federal_work_study_funds_spent_on_service",
                title_label="🧰 Fed Work-Study for Service (~4.76%)",
                description="Percentage of work-study funds spent on service",
                color_map=color_map,
                comparison_unis=comparison_unis
            )
        with col2:
            plot_chart_sorted(
                df=washington_filtered_tab[["Year", "IPEDS_Name", "%_of_grads_with_service_oriented_majors"]],
                metric_col="%_of_grads_with_service_oriented_majors",
                title_label="📘 Service-Oriented Majors (~4.76%)",
                description="% of students graduating in service-oriented disciplines",
                color_map=color_map,
                comparison_unis=comparison_unis
            )
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            plot_chart_sorted(
                df=washington_filtered_tab[["Year", "IPEDS_Name", "AmeriCorps/Peace_Corps_rank"]],
                metric_col="AmeriCorps/Peace_Corps_rank",
                title_label="🌍 AmeriCorps/Peace Corps (~4.76%)",
                description="Rank of participation in AmeriCorps and Peace Corps programs",
                color_map=color_map,
                comparison_unis=comparison_unis
            )
        with col2:
            plot_chart_sorted(
                df=washington_filtered_tab[["Year", "IPEDS_Name", "ROTC_rank"]],
                metric_col="ROTC_rank",
                title_label="🎖️ ROTC Program (~4.76%)",
                description="Rank of ROTC program size relative to enrollment",
                color_map=color_map,
                comparison_unis=comparison_unis
            )
