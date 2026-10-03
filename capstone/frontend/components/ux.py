import streamlit as st


def apply_workspace_styles() -> None:
    """Shared, theme-aligned presentation for the ExamIQ Streamlit pages."""
    st.markdown(
        """
        <style>
        .examiq-page-header { margin: .15rem 0 1.2rem; padding-bottom: .85rem; border-bottom: 1px solid #30363D; }
        .examiq-page-header h1 { margin: 0; color: #C9D1D9; font-size: 1.8rem; line-height: 1.2; }
        .examiq-page-header p { margin: .35rem 0 0; color: #8B949E; font-size: .92rem; }
        .examiq-eyebrow { color: #58A6FF !important; font-size: .72rem !important; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; margin-bottom: .3rem !important; }
        div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stHorizontalBlock"]) { min-width: 0; }
        div[data-testid="stButton"] button:focus-visible, div[data-testid="stLinkButton"] a:focus-visible,
        div[data-testid="stSelectbox"] div[role="combobox"]:focus-visible { outline: 2px solid #58A6FF; outline-offset: 2px; }
        div[data-testid="stButton"] button { transition: border-color .15s ease, background-color .15s ease; }
        div[data-testid="stButton"] button:hover { border-color: #58A6FF; }
        @media (max-width: 700px) {
            .examiq-page-header h1 { font-size: 1.5rem; }
            div[data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: .65rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, description: str, eyebrow: str = "ExamIQ workspace") -> None:
    st.markdown(
        f'<header class="examiq-page-header"><p class="examiq-eyebrow">{eyebrow}</p>'
        f'<h1>{title}</h1><p>{description}</p></header>',
        unsafe_allow_html=True,
    )
