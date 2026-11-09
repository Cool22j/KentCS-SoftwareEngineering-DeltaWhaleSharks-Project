import streamlit as st

st.set_page_config(
    page_title="Card Shark",
    page_icon=":material/style:",
    layout="wide",
)

from pages import *

st.logo("logo.png", size="large")

# create navigation bar
nv = st.navigation(
    [landing, rules, beginner, deckBuilder, deckInventory, cardCollection, account, edit],
    position="top",
)
nv.run()
