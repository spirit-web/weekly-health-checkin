from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="Torsdagsformulär", page_icon="📋", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
TABLE_URL = f"{SUPABASE_URL}/rest/v1/checkins"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

st.markdown("""
<style>
.block-container {
    padding-top: 1.2rem;
    max-width: 1680px;
}

.main-title {
    display: none;
}

p, label, span, div {
    font-size: 16px !important;
}

div[data-testid="stTabs"] button {
    font-size: 18px !important;
    font-weight: 750 !important;
}

.question-title {
    font-size: 22px !important;
    font-weight: 900;
    color: #111827;
    margin-bottom: 3px;
}

.goal-text {
    font-size: 15px !important;
    color: #374151;
    margin-bottom: 5px;
}

.answer-check {
    float: right;
    background: #179b43;
    color: white;
    border-radius: 999px;
    width: 28px;
    height: 28px;
    text-align: center;
    font-size: 20px !important;
    font-weight: 900;
    line-height: 28px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #f1f3f6 !important;
    border: 1px solid #d1d5db !important;
    border-radius: 15px !important;
    padding: 8px !important;
    min-height: 168px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.035) !important;
}

.st-key-card_q1_goal div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-card_q2_goal div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-card_q3_goal div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-card_q4_goal div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-card_q5_goal div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-card_q6_goal div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-card_q7_goal div[data-testid="stVerticalBlockBorderWrapper"],
.st-key-card_q8_goal div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #e7f7ec !important;
    border: 2px solid #69bd78 !important;
}

div[data-testid="stRadio"] label,
div[data-testid="stCheckbox"] label {
    font-size: 17px !important;
    font-weight: 750 !important;
    background: #f8fafc !important;
    border: 1px solid #d9dee7 !important;
    border-radius: 9px !important;
    padding: 6px 9px !important;
    margin: 1px 2px 1px 0 !important;
    min-width: 52px;
    justify-content: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.035);
}

.stButton > button[kind="primary"] {
    width: 100%;
    height: 56px !important;
    font-size: 23px !important;
    font-weight: 900 !important;
    border-radius: 12px !important;
    background: linear-gradient(90deg, #4028e8, #3222b8) !important;
    color: white !important;
}

.week-button button {
    min-height: 44px !important;
    background: #f2f4f7 !important;
    border: 1px solid #d1d5db !important;
    border-radius: 10px !important;
    font-size: 11px !important;
    font-weight: 800 !important;
    padding: 2px !important;
    white-space: pre-line !important;
}

.week-saved button {
    background: #e7f7ec !important;
    border: 2px solid #63bd75 !important;
}

.week-current button {
    border: 4px solid #2563eb !important;
}

hr {
    margin-top: 0.2rem !important;
    margin-bottom: 0.2rem !important;
}
</style>
""", unsafe_allow_html=True)


def load_data():
    response = requests.get(
        TABLE_URL,
        headers=HEADERS,
        params={"select": "*", "order": "created_at.asc"},
        timeout=20,
    )
    response.raise_for_status()
    df = pd.DataFrame(response.json())

    if df.empty:
        return df

    df["timestamp"] = pd.to_datetime(df["created_at"], errors="coerce")

    if "week_start" in df.columns:
        df["week_start"] = pd.to_datetime(df["week_start"], errors="coerce").dt.date

    numeric_cols = [
        "pipeline_jobs",
        "stress_0_10",
        "susanne_upplevd_tillganglighet_0_10",
        "susanne_faktisk_tillganglighet_0_10",
        "traningspass_7_dagar",
        "natur_timmar_7_dagar",
        "mail_svar_timmar",
        "morgonrutiner_man_tors",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def save_to_supabase(data):
    response = requests.post(TABLE_URL, headers=HEADERS, json=data, timeout=20)
    response.raise_for_status()


def update_row(row_id, data):
    response = requests.patch(
        f"{TABLE_URL}?id=eq.{row_id}",
        headers=HEADERS,
        json=data,
        timeout=20,
    )
    response.raise_for_status()


def delete_row(row_id):
    response = requests.delete(
        f"{TABLE_URL}?id=eq.{row_id}",
        headers=HEADERS,
        timeout=20,
    )
    response.raise_for_status()


def create_weeks():
    start = date(2026, 5, 11)
    end = date(2026, 9, 21)
    weeks = []
    current = start

    while current <= end:
        weeks.append({
            "start": current,
            "end": current + timedelta(days=6),
            "week": current.isocalendar().week,
            "month": current.month,
        })
        current += timedelta(days=7)

    return weeks


MONTH_SHORT = {5: "maj", 6: "jun", 7: "jul", 8: "aug", 9: "sep"}


def format_date_range(start, end):
    return f"{start.day} {MONTH_SHORT[start.month]}–{end.day} {MONTH_SHORT[end.month]}"


def monday_of_week(d):
    return d - timedelta(days=d.weekday())


def is_goal_met(q, value):
    if value is None:
        return False
    if q == 1:
        return value == "JA"
    if q == 2:
        return value <= 2
    if q == 3:
        return value <= 4
    if q == 4:
        return value >= 7
    if q == 5:
        return value >= 5
    if q == 6:
        return value >= 3
    if q == 7:
        return value <= 24
    if q == 8:
        return value >= 3
    return False


def is_answered(value):
    return value is not None


def question_container(q, goal):
    status = "goal" if goal else "neutral"
    return st.container(border=True, key=f"card_q{q}_{status}")


def question_header(number, title, goal_text, answered):
    if answered:
        st.markdown('<div class="answer-check">✓</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="question-title">{number}. {title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="goal-text">Mål: {goal_text}</div>', unsafe_allow_html=True)


def radio_choice(options, key, saved_value=None):
    index = None
    if saved_value in options:
        index = options.index(saved_value)

    return st.radio(
        "",
        options,
        index=index,
        horizontal=True,
        key=key,
        label_visibility="collapsed",
    )


def saved_weeks_from_df(df):
    if df.empty or "week_start" not in df.columns:
        return set()
    return set(df["week_start"].dropna().tolist())


def get_saved_row(df, selected_week):
    if df.empty or "week_start" not in df.columns:
        return None
    match = df[df["week_start"] == selected_week]
    if match.empty:
        return None
    return match.iloc[-1]


def get_value(row, col):
    if row is None:
        return None
    value = row.get(col)
    if pd.isna(value):
        return None
    return value


def morning_days_from_row(row):
    if row is None:
        return []
    raw = row.get("morning_days")
    if raw is None or pd.isna(raw) or raw == "":
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def closest_nature_label(value):
    if value is None:
        return None
    value = float(value)
    if value >= 3:
        return "3h"
    if value >= 2.5:
        return "2.5h"
    if value >= 2:
        return "2h"
    if value >= 1.5:
        return "1.5h"
    if value >= 1:
        return "1h"
    return "0.5h"


def closest_mail_label(value):
    if value is None:
        return None
    value = float(value)
    if value >= 96:
        return "4 dagar"
    if value >= 72:
        return "3 dagar"
    if value >= 48:
        return "2 dagar"
    if value >= 24:
        return "1 dag"
    return "Samma dag"


def build_payload(
    selected_week,
    lordagsgrunding,
    pipeline_jobs,
    stress_0_10,
    susanne_upplevd,
    susanne_faktisk,
    traningspass,
    natur_timmar,
    mail_svar_timmar,
    morgonrutiner,
    morning_days,
    kommentar,
):
    return {
        "week_start": selected_week.isoformat(),
        "lordagsgrunding": lordagsgrunding,
        "pipeline_jobs": int(pipeline_jobs),
        "stress_0_10": int(stress_0_10),
        "susanne_upplevd_tillganglighet_0_10": int(susanne_upplevd),
        "susanne_faktisk_tillganglighet_0_10": int(susanne_faktisk) if susanne_faktisk is not None else None,
        "traningspass_7_dagar": int(traningspass),
        "natur_timmar_7_dagar": float(natur_timmar),
        "mail_svar_timmar": float(mail_svar_timmar),
        "morgonrutiner_man_tors": int(morgonrutiner),
        "morning_days": ",".join(morning_days),
        "kommentar": kommentar,
    }


def add_analysis_scores(df):
    df = df.copy()

    df["pipeline_stress"] = (df["pipeline_jobs"].clip(0, 6) / 6) * 10
    df["stress_stress"] = df["stress_0_10"].clip(0, 10)
    df["tillganglighet_stress"] = 10 - df["susanne_upplevd_tillganglighet_0_10"].clip(0, 10)
    df["mail_stress"] = (df["mail_svar_timmar"].clip(0, 96) / 96) * 10

    df["Stressbelastning"] = df[
        ["pipeline_stress", "stress_stress", "tillganglighet_stress", "mail_stress"]
    ].mean(axis=1)

    df["lordagsgrunding_score"] = df["lordagsgrunding"].eq("JA").astype(int) * 10
    df["traning_score"] = (df["traningspass_7_dagar"].clip(0, 5) / 5) * 10
    df["natur_score"] = (df["natur_timmar_7_dagar"].clip(0, 3) / 3) * 10
    df["morgon_score"] = (df["morgonrutiner_man_tors"].clip(0, 3) / 3) * 10

    df["Hälsorutiner"] = df[
        ["lordagsgrunding_score", "traning_score", "natur_score", "morgon_score"]
    ].mean(axis=1)

    df["veckonummer"] = df["week_start"].apply(lambda x: f"v.{x.isocalendar().week}")

    return df


weeks = create_weeks()

if "selected_week_start" not in st.session_state:
    possible_starts = [w["start"] for w in weeks]
    today_monday = monday_of_week(date.today())
    st.session_state.selected_week_start = today_monday if today_monday in possible_starts else possible_starts[0]

selected_week = st.session_state.selected_week_start

st.markdown('<div class="main-title">Torsdagsformulär 10:30</div>', unsafe_allow_html=True)

tab_form, tab_analysis, tab_admin = st.tabs(["📝 Formulär", "📊 Analys", "🛠️ Admin"])

with tab_form:
    df = load_data()
    saved_weeks = saved_weeks_from_df(df)
    saved_row = get_saved_row(df, selected_week)
    week_is_saved = saved_row is not None

    natur_map = {
        "0.5h": 0.5,
        "1h": 1.0,
        "1.5h": 1.5,
        "2h": 2.0,
        "2.5h": 2.5,
        "3h": 3.0,
    }

    mail_map = {
        "Samma dag": 0,
        "1 dag": 24,
        "2 dagar": 48,
        "3 dagar": 72,
        "4 dagar": 96,
    }

    saved_days = morning_days_from_row(saved_row)

    saved_natur = get_value(saved_row, "natur_timmar_7_dagar")
    saved_mail = get_value(saved_row, "mail_svar_timmar")

    row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)

    with row1_col1:
        saved = get_value(saved_row, "lordagsgrunding")
        current_value = st.session_state.get(f"q1_{selected_week}", saved)
        goal = is_goal_met(1, current_value)
        answered = is_answered(current_value)
        with question_container(1, goal):
            question_header(1, "Lördagsgrunding", "JA", answered)
            lordagsgrunding = radio_choice(["JA", "NEJ"], f"q1_{selected_week}", saved)

    with row1_col2:
        saved = get_value(saved_row, "pipeline_jobs")
        saved_int = int(saved) if saved is not None else None
        current_value = st.session_state.get(f"q2_{selected_week}", saved_int)
        goal = is_goal_met(2, current_value)
        answered = is_answered(current_value)
        with question_container(2, goal):
            question_header(2, "Jobb i pipelinen", "1–2 jobb", answered)
            pipeline_jobs = radio_choice([0, 1, 2, 3, 4, 5, 6], f"q2_{selected_week}", saved_int)

    with row1_col3:
        saved = get_value(saved_row, "stress_0_10")
        saved_int = int(saved) if saved is not None else None
        current_value = st.session_state.get(f"q3_{selected_week}", saved_int)
        goal = is_goal_met(3, current_value)
        answered = is_answered(current_value)
        with question_container(3, goal):
            question_header(3, "Stress", "1–4", answered)
            stress_0_10 = radio_choice(list(range(1, 11)), f"q3_{selected_week}", saved_int)

    with row1_col4:
        saved = get_value(saved_row, "susanne_upplevd_tillganglighet_0_10")
        saved_int = int(saved) if saved is not None else None
        current_value = st.session_state.get(f"q4_{selected_week}", saved_int)
        goal = is_goal_met(4, current_value)
        answered = is_answered(current_value)
        with question_container(4, goal):
            question_header(4, "Tillgänglighet", "7–10", answered)
            susanne_upplevd = radio_choice(list(range(1, 11)), f"q4_{selected_week}", saved_int)

    row2_col1, row2_col2, row2_col3, row2_col4 = st.columns(4)

    with row2_col1:
        saved = get_value(saved_row, "traningspass_7_dagar")
        saved_int = int(saved) if saved is not None else None
        current_value = st.session_state.get(f"q5_{selected_week}", saved_int)
        goal = is_goal_met(5, current_value)
        answered = is_answered(current_value)
        with question_container(5, goal):
            question_header(5, "Träning", "minst 5 pass", answered)
            traningspass = radio_choice([0, 1, 2, 3, 4, 5, 6, 7], f"q5_{selected_week}", saved_int)

    with row2_col2:
        saved_label = closest_nature_label(saved_natur)
        current_label = st.session_state.get(f"q6_{selected_week}", saved_label)
        current_value = natur_map.get(current_label)
        goal = is_goal_met(6, current_value)
        answered = is_answered(current_value)
        with question_container(6, goal):
            question_header(6, "Naturtid", "minst 3 timmar", answered)
            natur_label = radio_choice(list(natur_map.keys()), f"q6_{selected_week}", saved_label)
            natur_timmar = natur_map.get(natur_label)

    with row2_col3:
        saved_label = closest_mail_label(saved_mail)
        current_label = st.session_state.get(f"q7_{selected_week}", saved_label)
        current_value = mail_map.get(current_label)
        goal = is_goal_met(7, current_value)
        answered = is_answered(current_value)
        with question_container(7, goal):
            question_header(7, "Mailsvar", "samma dag eller 1 dag", answered)
            mail_label = radio_choice(list(mail_map.keys()), f"q7_{selected_week}", saved_label)
            mail_svar_timmar = mail_map.get(mail_label)

    with row2_col4:
        mon_key = f"mon_{selected_week}"
        tis_key = f"tis_{selected_week}"
        ons_key = f"ons_{selected_week}"
        tors_key = f"tors_{selected_week}"

        current_morning_count = sum([
            st.session_state.get(mon_key, "Mån" in saved_days),
            st.session_state.get(tis_key, "Tis" in saved_days),
            st.session_state.get(ons_key, "Ons" in saved_days),
            st.session_state.get(tors_key, "Tors" in saved_days),
        ])

        goal = is_goal_met(8, current_morning_count)
        answered = current_morning_count > 0

        with question_container(8, goal):
            question_header(8, "Morgonrutiner", "minst 3 av 4 dagar", answered)

            d1, d2 = st.columns(2)
            d3, d4 = st.columns(2)

            with d1:
                mon = st.checkbox("Mån", key=mon_key, value="Mån" in saved_days)
            with d2:
                tis = st.checkbox("Tis", key=tis_key, value="Tis" in saved_days)
            with d3:
                ons = st.checkbox("Ons", key=ons_key, value="Ons" in saved_days)
            with d4:
                tors = st.checkbox("Tors", key=tors_key, value="Tors" in saved_days)

            morning_days = []
            if mon:
                morning_days.append("Mån")
            if tis:
                morning_days.append("Tis")
            if ons:
                morning_days.append("Ons")
            if tors:
                morning_days.append("Tors")

            morgonrutiner = len(morning_days)

    with st.expander("Bonus: Susannes faktiska upplevelse, valfritt"):
        saved = get_value(saved_row, "susanne_faktisk_tillganglighet_0_10")
        saved_int = int(saved) if saved is not None else None
        susanne_faktisk = radio_choice(list(range(1, 11)), f"bonus_{selected_week}", saved_int)
        kommentar = st.text_area("Kort kommentar, valfritt", value=get_value(saved_row, "kommentar") or "")

    st.markdown("---")
    st.markdown("### Veckor")

    week_rows = [weeks[:10], weeks[10:]]

    for week_row in week_rows:
        timeline_cols = st.columns(len(week_row))

        for col, week in zip(timeline_cols, week_row):
            with col:
                is_saved = week["start"] in saved_weeks
                is_current = week["start"] == selected_week

                saved_icon = " ✅" if is_saved else ""
                current_icon = "▶ " if is_current else ""

                button_label = f"{current_icon}v.{week['week']}: {format_date_range(week['start'], week['end'])}{saved_icon}"
                
                css_class = "week-button"
                if is_saved:
                    css_class += " week-saved"
                if is_current:
                    css_class += " week-current"

                with st.container(key=f"week_card_{week['start']}"):
                    st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)

                    if st.button(
                        button_label,
                        key=f"select_{week['start']}",
                        use_container_width=True,
                    ):
                        st.session_state.selected_week_start = week["start"]
                        st.rerun()

                    st.markdown("</div>", unsafe_allow_html=True)

    submitted = st.button(
        "💾 SPARA VECKANS SVAR",
        type="primary",
        use_container_width=True,
        disabled=week_is_saved,
    )

    if submitted:
        required_values = [
            lordagsgrunding,
            pipeline_jobs,
            stress_0_10,
            susanne_upplevd,
            traningspass,
            natur_timmar,
            mail_svar_timmar,
        ]

        if any(value is None for value in required_values):
            st.error("Fyll i alla huvudfrågor innan du sparar.")
        else:
            data = build_payload(
                selected_week,
                lordagsgrunding,
                pipeline_jobs,
                stress_0_10,
                susanne_upplevd,
                susanne_faktisk,
                traningspass,
                natur_timmar,
                mail_svar_timmar,
                morgonrutiner,
                morning_days,
                kommentar,
            )

            try:
                save_to_supabase(data)
                st.success("Veckans svar sparades ✅")
                st.rerun()
            except Exception as e:
                st.error("Kunde inte spara svaret.")
                st.exception(e)


with tab_analysis:
    st.header("Analys")

    try:
        df = load_data()

        if df.empty:
            st.info("Inga svar sparade ännu.")
        else:
            df = df.sort_values("week_start")

            df["mål_lördagsgrunding"] = df["lordagsgrunding"] == "JA"
            df["mål_pipeline"] = df["pipeline_jobs"] <= 2
            df["mål_stress"] = df["stress_0_10"] <= 4
            df["mål_tillgänglighet"] = df["susanne_upplevd_tillganglighet_0_10"] >= 7
            df["mål_träning"] = df["traningspass_7_dagar"] >= 5
            df["mål_natur"] = df["natur_timmar_7_dagar"] >= 3
            df["mål_mailsvar"] = df["mail_svar_timmar"] <= 24
            df["mål_morgonrutiner"] = df["morgonrutiner_man_tors"] >= 3

            goal_cols = [
                "mål_lördagsgrunding",
                "mål_pipeline",
                "mål_stress",
                "mål_tillgänglighet",
                "mål_träning",
                "mål_natur",
                "mål_mailsvar",
                "mål_morgonrutiner",
            ]

            df["antal_mål_uppnådda"] = df[goal_cols].sum(axis=1)
            df = add_analysis_scores(df)

            st.subheader("Hur många mål uppnåddes varje vecka?")

            fig2 = px.bar(
                df,
                x="veckonummer",
                y="antal_mål_uppnådda",
                range_y=[0, 8],
                text="antal_mål_uppnådda",
                labels={
                    "veckonummer": "VECKA",
                    "antal_mål_uppnådda": "ANTAL MÅL",
                },
            )
            fig2.update_layout(font=dict(size=18))
            fig2.update_traces(textfont_size=18)
            st.plotly_chart(fig2, use_container_width=True)

            st.subheader("Vilka mål uppnås oftast?")

            goal_labels = {
                "mål_lördagsgrunding": "LÖRDAGSGRUNDING",
                "mål_pipeline": "PIPELINE",
                "mål_stress": "STRESS",
                "mål_tillgänglighet": "TILLGÄNGLIGHET",
                "mål_träning": "TRÄNING",
                "mål_natur": "NATUR",
                "mål_mailsvar": "MAILSVAR",
                "mål_morgonrutiner": "MORGONRUTINER",
            }

            goal_rate = df[goal_cols].mean().reset_index()
            goal_rate.columns = ["Mål", "Andel uppnådda veckor"]
            goal_rate["Mål"] = goal_rate["Mål"].map(goal_labels)

            fig3 = px.bar(
                goal_rate,
                x="Mål",
                y="Andel uppnådda veckor",
                range_y=[0, 1],
                text_auto=".0%",
            )
            fig3.update_layout(
                font=dict(size=18),
                xaxis_title="MÅL",
                yaxis_title="ANDEL UPPNÅDDA VECKOR",
            )
            fig3.update_traces(textfont_size=18)
            st.plotly_chart(fig3, use_container_width=True)

            st.subheader("Veckobalans: stressbelastning och hälsorutiner")

            st.info(
                "Grafen visar två sammanfattande mått per vecka på skalan 0–10. "
                "Stressbelastning bygger på pipeline, stress, tillgänglighet och mailsvar. "
                "Hälsorutiner bygger på lördagsgrunding, träning, naturtid och morgonrutiner. "
                "Högre stressbelastning betyder mer press. "
                "Högre hälsorutiner betyder bättre återhämtning."
            )

            score_df = df[["veckonummer", "Stressbelastning", "Hälsorutiner"]].melt(
                id_vars="veckonummer",
                var_name="Mätning",
                value_name="Värde",
            )
            fig1 = px.line(
                score_df,
                x="veckonummer",
                y="Värde",
                color="Mätning",
                markers=True,
                range_y=[0, 10],
                color_discrete_map={
                    "Stressbelastning": "orange",
                    "Hälsorutiner": "green",
                },
                labels={
                    "veckonummer": "VECKA",
                    "Värde": "VÄRDE 0–10",
                    "Mätning": "MÄTVÄRDE",
                },
            )
            fig1.update_layout(font=dict(size=18))
            fig1.update_traces(line=dict(width=4), marker=dict(size=10))
            st.plotly_chart(fig1, use_container_width=True)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Antal veckor", len(df))
            c2.metric("Snitt stressbelastning", round(df["Stressbelastning"].mean(), 1))
            c3.metric("Snitt hälsorutiner", round(df["Hälsorutiner"].mean(), 1))
            c4.metric("Snitt mål/vecka", round(df["antal_mål_uppnådda"].mean(), 1))

            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error("Kunde inte läsa analysdata.")
        st.exception(e)


with tab_admin:
    st.header("Admin: ändra eller radera vecka")

    try:
        df = load_data()

        if df.empty:
            st.info("Inga svar att administrera ännu.")
        else:
            df = df.sort_values("week_start")
            week_options = df["week_start"].dropna().tolist()

            selected_admin_week = st.selectbox(
                "Välj vecka att ändra eller radera",
                week_options,
                format_func=lambda x: f"v.{x.isocalendar().week} ({format_date_range(x, x + timedelta(days=6))})",
            )

            admin_row = get_saved_row(df, selected_admin_week)

            if admin_row is not None:
                st.info(
                    f"Du ändrar v.{selected_admin_week.isocalendar().week}: "
                    f"{format_date_range(selected_admin_week, selected_admin_week + timedelta(days=6))}"
                )

                admin_days = morning_days_from_row(admin_row)

                natur_map = {
                    "0.5h": 0.5,
                    "1h": 1.0,
                    "1.5h": 1.5,
                    "2h": 2.0,
                    "2.5h": 2.5,
                    "3h": 3.0,
                }

                mail_map = {
                    "Samma dag": 0,
                    "1 dag": 24,
                    "2 dagar": 48,
                    "3 dagar": 72,
                    "4 dagar": 96,
                }

                c1, c2, c3, c4 = st.columns(4)

                with c1:
                    edit_lordag = st.radio(
                        "1. Lördagsgrunding",
                        ["JA", "NEJ"],
                        horizontal=True,
                        index=["JA", "NEJ"].index(admin_row["lordagsgrunding"]),
                    )

                with c2:
                    edit_pipeline = st.radio(
                        "2. Jobb i pipelinen",
                        [0, 1, 2, 3, 4, 5, 6],
                        horizontal=True,
                        index=[0, 1, 2, 3, 4, 5, 6].index(int(admin_row["pipeline_jobs"])),
                    )

                with c3:
                    edit_stress = st.radio(
                        "3. Stress",
                        list(range(1, 11)),
                        horizontal=True,
                        index=list(range(1, 11)).index(int(admin_row["stress_0_10"])),
                    )

                with c4:
                    edit_tillg = st.radio(
                        "4. Tillgänglighet",
                        list(range(1, 11)),
                        horizontal=True,
                        index=list(range(1, 11)).index(int(admin_row["susanne_upplevd_tillganglighet_0_10"])),
                    )

                c5, c6, c7, c8 = st.columns(4)

                with c5:
                    edit_training = st.radio(
                        "5. Träning",
                        [0, 1, 2, 3, 4, 5, 6, 7],
                        horizontal=True,
                        index=[0, 1, 2, 3, 4, 5, 6, 7].index(int(admin_row["traningspass_7_dagar"])),
                    )

                with c6:
                    nature_values = list(natur_map.values())
                    nature_labels = list(natur_map.keys())
                    edit_nature_label = st.radio(
                        "6. Naturtid",
                        nature_labels,
                        horizontal=True,
                        index=nature_values.index(float(admin_row["natur_timmar_7_dagar"]))
                        if float(admin_row["natur_timmar_7_dagar"]) in nature_values
                        else len(nature_values) - 1,
                    )

                with c7:
                    mail_values = list(mail_map.values())
                    mail_labels = list(mail_map.keys())
                    edit_mail_label = st.radio(
                        "7. Mailsvar",
                        mail_labels,
                        horizontal=True,
                        index=mail_values.index(float(admin_row["mail_svar_timmar"]))
                        if float(admin_row["mail_svar_timmar"]) in mail_values
                        else len(mail_values) - 1,
                    )

                with c8:
                    st.markdown("**8. Morgonrutiner**")
                    edit_days = []
                    if st.checkbox("Mån", value="Mån" in admin_days, key="admin_mån"):
                        edit_days.append("Mån")
                    if st.checkbox("Tis", value="Tis" in admin_days, key="admin_tis"):
                        edit_days.append("Tis")
                    if st.checkbox("Ons", value="Ons" in admin_days, key="admin_ons"):
                        edit_days.append("Ons")
                    if st.checkbox("Tors", value="Tors" in admin_days, key="admin_tors"):
                        edit_days.append("Tors")

                edit_comment = st.text_area("Kommentar", value=admin_row.get("kommentar") or "")

                if st.button("💾 Uppdatera vald vecka", type="primary", use_container_width=True):
                    payload = build_payload(
                        selected_admin_week,
                        edit_lordag,
                        edit_pipeline,
                        edit_stress,
                        edit_tillg,
                        None,
                        edit_training,
                        natur_map[edit_nature_label],
                        mail_map[edit_mail_label],
                        len(edit_days),
                        edit_days,
                        edit_comment,
                    )
                    update_row(int(admin_row["id"]), payload)
                    st.success("Veckan uppdaterades ✅")
                    st.rerun()

                if st.button("🗑️ Radera vald vecka", use_container_width=True):
                    delete_row(int(admin_row["id"]))
                    st.success("Veckan raderades ✅")
                    st.rerun()

    except Exception as e:
        st.error("Kunde inte läsa admin-data.")
        st.exception(e)