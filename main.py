import pymongo
import streamlit as st

st.set_page_config(
    page_title="Card Shark",
    page_icon=":material/style:",
    layout="wide",
)

from pages import *
import user_database as udb
import users

COOKIE_NAME = "cardshark_session"

if not st.session_state.get("user_id"):
    token = st.context.cookies.get(COOKIE_NAME)
    if token:
        try:
            uid = udb.get_session_user_id(token)
            user = users.get_user(uid) if uid else None
        except (pymongo.errors.PyMongoError, RuntimeError):
            user = None
        if user:
            st.session_state["user_id"] = user["_id"]
            st.session_state["username"] = user["username"]
            st.session_state["session_token"] = token

st.logo("logo.png", size="large")

# create navigation bar
nv = st.navigation(
    [landing, rules, beginner, deckBuilder, deckInventory, cardCollection, account, edit],
    position="top",
)
nv.run()