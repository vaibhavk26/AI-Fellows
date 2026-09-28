from collections import defaultdict
from html import escape

import altair as alt
import pandas as pd
import streamlit as st


_STATUS_COLORS = {
    "needs_practice": "#FF8B82",
    "good": "#E3B341",
    "strong": "#56D4A7",
}
_SUBJECT_STATUS_COLORS = {
    "needs_practice": "#F85149",
    "good": "#D29922",
    "strong": "#3FB950",
}


def _percentage(row: dict) -> float:
    try:
        return max(0.0, min(100.0, float(row.get("score_percentage") or 0)))
    except (TypeError, ValueError):
        return 0.0


def _status(score: float) -> str:
    if score >= 80:
        return "strong"
    if score >= 60:
        return "good"
    return "needs_practice"


def apply_dashboard_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --dashboard-text: #C9D1D9;
            --dashboard-text-muted: #8B949E;
            --dashboard-panel: #161B22;
            --dashboard-border: #30363D;
        }
        .dashboard-header {
            display: flex; align-items: center; justify-content: space-between;
            gap: 1rem; margin: 0.2rem 0 1.25rem;
        }
        .dashboard-header .eyebrow {
            color: #58A6FF; font-size: 0.72rem; font-weight: 700;
            text-transform: uppercase; margin: 0 0 0.25rem;
        }
        .dashboard-header h1 {
            color: var(--dashboard-text); font-family: inherit;
            font-size: 1.8rem; font-weight: 650; line-height: 1.2; margin: 0;
        }
        .dashboard-student {
            color: var(--dashboard-text); background: var(--dashboard-panel); border: 1px solid var(--dashboard-border);
            border-radius: 999px; padding: 0.45rem 0.8rem; font-size: 0.9rem;
        }
        .kpi-grid {
            display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.75rem; margin: 0.5rem 0 1.4rem;
        }
        .kpi-card {
            min-height: 112px; box-sizing: border-box; background: var(--dashboard-panel);
            border: 1px solid var(--dashboard-border); border-radius: 8px; padding: 1rem 1.05rem;
        }
        .kpi-label { color: var(--dashboard-text-muted); font-size: 0.82rem; margin-bottom: 0.5rem; }
        .kpi-value {
            color: var(--dashboard-text); font-family: inherit;
            font-size: 1.7rem; font-weight: 650; line-height: 1.1;
        }
        .kpi-note { color: var(--dashboard-text-muted); font-size: 0.76rem; margin-top: 0.45rem; }
        .kpi-note.positive { color: #56D4A7; }
        .kpi-note.negative { color: #FF8B82; }
        .dashboard-section { margin: 1.55rem 0 0.45rem; }
        .dashboard-section h2 {
            color: var(--dashboard-text); font-family: inherit;
            font-size: 1.15rem; font-weight: 650; margin: 0;
        }
        .dashboard-section p { color: var(--dashboard-text-muted); font-size: 0.83rem; margin: 0.2rem 0 0.7rem; }
        .chapter-grid {
            display: grid; gap: 0.5rem; padding: 0.75rem;
            border: 1px solid var(--dashboard-border); border-radius: 8px;
            background: transparent;
        }
        .chapter-row {
            display: grid; grid-template-columns: minmax(150px, 1.1fr) minmax(110px, 2fr) 54px;
            align-items: center; gap: 0.8rem; border-radius: 6px; padding: 0.6rem 0.75rem;
            border: 1px solid var(--dashboard-border);
        }
        .chapter-name { color: var(--dashboard-text); font-size: 0.86rem; overflow-wrap: anywhere; }
        .chapter-track, .topic-track {
            height: 7px; overflow: hidden; background: var(--dashboard-border); border-radius: 99px;
        }
        .chapter-fill, .topic-fill { height: 100%; border-radius: 99px; }
        .chapter-score { color: var(--dashboard-text); font-size: 0.83rem; font-weight: 650; text-align: right; }
        .chapter-legend { display: flex; flex-wrap: wrap; gap: 0.45rem 1rem; margin: 0 0 0.65rem; }
        .chapter-legend span { color: var(--dashboard-text-muted); font-size: 0.75rem; }
        .chapter-legend i { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 0.3rem; }
        .topic-list { display: grid; gap: 0.55rem; padding: 0.3rem 0.15rem 0.65rem; }
        .topic-row {
            display: grid; grid-template-columns: minmax(140px, 1.4fr) minmax(90px, 2fr) 52px;
            align-items: center; gap: 0.75rem;
        }
        .topic-name { color: var(--dashboard-text); font-size: 0.84rem; overflow-wrap: anywhere; }
        .topic-score { color: var(--dashboard-text); font-size: 0.82rem; font-variant-numeric: tabular-nums; text-align: right; }
        @media (max-width: 850px) {
            .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        }
        @media (max-width: 520px) {
            .kpi-grid { grid-template-columns: 1fr; }
            .dashboard-header { align-items: flex-start; flex-direction: column; }
            .chapter-row { grid-template-columns: minmax(100px, 1fr) minmax(70px, 1fr) 46px; gap: 0.45rem; }
            .topic-row { grid-template-columns: minmax(100px, 1.2fr) minmax(55px, 1fr) 46px; gap: 0.45rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(student_name: str | None) -> None:
    safe_name = escape(student_name or "Student")
    st.markdown(
        f"""
        <header class="dashboard-header">
            <div><p class="eyebrow">Learning analytics</p><h1>Student Performance</h1></div>
            <div class="dashboard-student">{safe_name}</div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_kpis(summary: dict, attempts: list[dict]) -> None:
    attempt_count = int(summary.get("attempts") or 0)
    overall = _percentage({"score_percentage": summary.get("score_percentage")})
    if not attempt_count:
        overall_label = "N/A"
        improvement_value = "N/A"
        improvement_note = "Complete two exams to see a trend"
        improvement_class = ""
    else:
        overall_label = f"{overall:.1f}%"
        ordered = sorted(attempts, key=lambda row: str(row.get("submitted_at") or ""))
        if len(ordered) >= 2:
            improvement = _percentage(ordered[-1]) - _percentage(ordered[-2])
            improvement_value = f"{improvement:+.1f} pts"
            improvement_note = "vs. previous attempt"
            improvement_class = "positive" if improvement >= 0 else "negative"
        else:
            improvement_value = "N/A"
            improvement_note = "Complete another exam to compare"
            improvement_class = ""

    cards = [
        ("Overall performance", overall_label, f"{summary.get('score', 0)} / {summary.get('max_score', 0)} marks", ""),
        ("Exam attempts", str(attempt_count), "Submitted exams in this view", ""),
        ("Questions answered", str(int(summary.get("questions_answered") or 0)), "Across submitted exams", ""),
        ("Progress", improvement_value, improvement_note, improvement_class),
    ]
    card_markup = "".join(
        f'<div class="kpi-card"><div class="kpi-label">{escape(label)}</div>'
        f'<div class="kpi-value">{escape(value)}</div>'
        f'<div class="kpi-note {escape(note_class)}">{escape(note)}</div></div>'
        for label, value, note, note_class in cards
    )
    st.markdown(f'<div class="kpi-grid">{card_markup}</div>', unsafe_allow_html=True)


def render_section(title: str, subtitle: str | None = None) -> None:
    detail = f"<p>{escape(subtitle)}</p>" if subtitle else ""
    st.markdown(
        f'<div class="dashboard-section"><h2>{escape(title)}</h2>{detail}</div>',
        unsafe_allow_html=True,
    )


def render_attempt_trend(attempts: list[dict]) -> None:
    if not attempts:
        st.info("Complete an exam to see your progress over time.")
        return

    ordered = sorted(attempts, key=lambda row: str(row.get("submitted_at") or ""))
    chart_rows = [
        {
            "attempt_no": index,
            "exam": str(row.get("exam_title") or "Exam"),
            "submitted": str(row.get("submitted_at") or "")[:19].replace("T", " "),
            "score_percentage": _percentage(row),
        }
        for index, row in enumerate(ordered, start=1)
    ]
    line_data = pd.DataFrame(chart_rows)
    line = alt.Chart(line_data).mark_line(
        color="#58A6FF",
        strokeWidth=2.5,
        interpolate="monotone",
        point=alt.OverlayMarkDef(filled=True, size=58, color="#58A6FF"),
    ).encode(
        x=alt.X("attempt_no:Q", title="Exam attempt", axis=alt.Axis(tickMinStep=1, grid=False)),
        y=alt.Y(
            "score_percentage:Q",
            title="Score",
            scale=alt.Scale(domain=[0, 100]),
            axis=alt.Axis(labelExpr="datum.value + '%'", gridColor="#30363D", tickCount=5),
        ),
        tooltip=[
            alt.Tooltip("attempt_no:Q", title="Attempt", format=".0f"),
            alt.Tooltip("exam:N", title="Exam"),
            alt.Tooltip("submitted:N", title="Submitted"),
            alt.Tooltip("score_percentage:Q", title="Score", format=".1f"),
        ],
    )
    target = alt.Chart(pd.DataFrame([{"target": 80}])).mark_rule(
        color="#8B949E", strokeDash=[4, 4], strokeWidth=1
    ).encode(
        y=alt.Y("target:Q"),
        tooltip=alt.Tooltip("target:Q", title="Strong performance reference", format=".0f"),
    )
    latest = alt.Chart(pd.DataFrame([chart_rows[-1]])).mark_point(
        filled=True, color="#161B22", stroke="#79C0FF", strokeWidth=2, size=115
    ).encode(
        x="attempt_no:Q",
        y="score_percentage:Q",
        tooltip=[
            alt.Tooltip("exam:N", title="Latest exam"),
            alt.Tooltip("score_percentage:Q", title="Latest score", format=".1f"),
        ],
    )
    chart = alt.layer(target, line, latest).properties(height=285).configure_view(stroke=None).configure_axis(
        labelColor="#C9D1D9",
        titleColor="#8B949E",
        domainColor="#30363D",
        tickColor="#30363D",
        labelFont="sans-serif",
        titleFont="sans-serif",
    )
    st.altair_chart(chart, use_container_width=True)


def render_subject_performance(rows: list[dict]) -> None:
    if not rows:
        st.info("No subject scores for the selected filters.")
        return
    chart_rows = [
        {
            "subject": str(row.get("name") or "Unnamed subject"),
            "score": _percentage(row),
            "score_label": f"{_percentage(row):.1f}%",
            "status": _status(_percentage(row)),
            "attempts": row.get("attempts", 0),
        }
        for row in rows
    ]
    chart_data = pd.DataFrame(chart_rows)
    bars = alt.Chart(chart_data).mark_bar(height=17, cornerRadiusEnd=5).encode(
        x=alt.X(
            "score:Q",
            title="Average score",
            scale=alt.Scale(domain=[0, 112]),
            axis=alt.Axis(values=[0, 20, 40, 60, 80, 100], labelExpr="datum.value + '%'", gridColor="#30363D"),
        ),
        y=alt.Y(
            "subject:N",
            title=None,
            sort=alt.EncodingSortField(field="score", order="descending"),
            axis=alt.Axis(labelLimit=260, ticks=False, domain=False),
        ),
        color=alt.Color(
            "status:N",
            scale=alt.Scale(
                domain=["strong", "good", "needs_practice"],
                range=[
                    _SUBJECT_STATUS_COLORS["strong"],
                    _SUBJECT_STATUS_COLORS["good"],
                    _SUBJECT_STATUS_COLORS["needs_practice"],
                ],
            ),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("subject:N", title="Subject"),
            alt.Tooltip("score:Q", title="Average score (%)", format=".1f"),
            alt.Tooltip("attempts:Q", title="Attempts"),
            alt.Tooltip("status:N", title="Level"),
        ],
    )
    labels = alt.Chart(chart_data).mark_text(align="left", dx=7, color="#C9D1D9", fontSize=12).encode(
        x="score:Q",
        y=alt.Y("subject:N", sort=alt.EncodingSortField(field="score", order="descending")),
        text="score_label:N",
    )
    chart = alt.layer(bars, labels).properties(height=max(120, min(480, 30 * len(chart_rows))))
    chart = chart.configure_view(stroke="#30363D", strokeWidth=1, fill="transparent").configure_axis(
        labelColor="#C9D1D9",
        titleColor="#8B949E",
        domainColor="#30363D",
        tickColor="#30363D",
        labelFont="Aptos",
        titleFont="Aptos",
    )
    st.altair_chart(chart, use_container_width=True)


def render_chapter_heatmap(rows: list[dict]) -> None:
    if not rows:
        st.info("No chapter scores for the selected filters.")
        return
    st.markdown(
        "<div class=\"chapter-legend\">"
        f"<span><i style=\"background:{_STATUS_COLORS['strong']}\"></i>Strong - 80%+</span>"
        f"<span><i style=\"background:{_STATUS_COLORS['good']}\"></i>Developing - 60-79%</span>"
        f"<span><i style=\"background:{_STATUS_COLORS['needs_practice']}\"></i>Needs attention - under 60%</span>"
        "</div>",
        unsafe_allow_html=True,
    )
    items = sorted(rows, key=lambda row: (str(row.get("subject_name") or ""), _percentage(row)))
    markup = ['<div class="chapter-grid">']
    for row in items:
        score = _percentage(row)
        band = _status(score)
        name = " / ".join(
            part for part in (str(row.get("subject_name") or ""), str(row.get("name") or "Unnamed chapter")) if part
        )
        markup.append(
            f'<div class="chapter-row {band}" title="{escape(name)}: {score:.1f}%">'
            f'<span class="chapter-name">{escape(name)}</span>'
            f'<span class="chapter-track"><span class="chapter-fill" style="display:block;width:{score:.1f}%;background:{_STATUS_COLORS[band]}"></span></span>'
            f'<strong class="chapter-score">{score:.1f}%</strong></div>'
        )
    markup.append("</div>")
    st.markdown("".join(markup), unsafe_allow_html=True)


def render_topic_matrix(rows: list[dict]) -> None:
    if not rows:
        st.info("No topic scores for the selected filters.")
        return
    grouped = defaultdict(list)
    for row in rows:
        key = (str(row.get("subject_name") or "Subject"), str(row.get("chapter_name") or "Unassigned chapter"))
        grouped[key].append(row)

    for index, ((subject_name, chapter_name), topics) in enumerate(sorted(grouped.items())):
        title = f"{chapter_name} / {subject_name} / {len(topics)} topics"
        with st.expander(title, expanded=index == 0):
            markup = ['<div class="topic-list">']
            for row in sorted(topics, key=lambda item: _percentage(item), reverse=True):
                score = _percentage(row)
                band = _status(score)
                topic_name = escape(str(row.get("name") or "Unnamed topic"))
                markup.append(
                    f'<div class="topic-row" title="{topic_name}: {score:.1f}%">'
                    f'<span class="topic-name">{topic_name}</span>'
                    f'<span class="topic-track"><span class="topic-fill" style="display:block;width:{score:.1f}%;background:{_STATUS_COLORS[band]}"></span></span>'
                    f'<span class="topic-score">{score:.1f}%</span></div>'
                )
            markup.append("</div>")
            st.markdown("".join(markup), unsafe_allow_html=True)
