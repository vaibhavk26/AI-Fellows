import streamlit as st

from components.api import clear_session


def render_account_controls(user: dict | None) -> None:
    """Show the app identity and account action beneath Streamlit's page navigation."""
    with st.sidebar:
        st.markdown("## ExamIQ")
        if user:
            st.caption(f"{user['full_name']}  ·  {user['role'].title()}")
            if st.button("Sign out", key="sidebar_sign_out", use_container_width=True):
                clear_session()
                st.rerun()
