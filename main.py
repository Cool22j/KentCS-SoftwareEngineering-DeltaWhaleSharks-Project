import streamlit as st
from pages import *

st.logo("logo.png", size = "large")

#create navigation bar
nv = st.navigation(
    [landing, rules, beginner, deckBuilder, deckInventory, account, edit],
    position = "top"
)
nv.run()