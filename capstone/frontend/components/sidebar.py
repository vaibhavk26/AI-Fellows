import streamlit as st

from components.api import clear_session


def render() -> None:
	user = st.session_state.get("user")
	with st.sidebar:
		st.markdown("## Capstone Learning")
		if user:
			st.caption(f"{user['full_name']}  ·  {user['role'].title()}")
			if st.button("Sign out", use_container_width=True):
				clear_session()
				st.rerun()
		else:
			st.info("Sign in on the home page.")
