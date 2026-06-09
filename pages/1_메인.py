import streamlit as st

st.set_page_config(layout="wide")

st.title("MAIN TEST")

st.write("SESSION STATE")

st.write(st.session_state)

if st.button("새로고침 테스트"):

    st.rerun()