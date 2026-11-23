import pymongo
import streamlit as st
import streamlit.components.v1 as components

import user_database as udb
import users

COOKIE_NAME = "cardshark_session"
SESSION_SECONDS = udb.SESSION_DAYS * 24 * 3600

st.markdown(
    "<h1 style='text-align: center;'>Your Account</h1>",
    unsafe_allow_html=True,
)


def _sign_in(user):
    """Remember the logged-in user for this session."""
    st.session_state["user_id"] = user["_id"]
    st.session_state["username"] = user["username"]
    try:
        token = udb.create_session(user["_id"])
    except (pymongo.errors.PyMongoError, RuntimeError):
        return None
    st.session_state["session_token"] = token
    return token


def _finish_login(token):
    """Write the cookie from the browser, then let the user continue."""
    if not token:
        st.switch_page("landing.py")
    components.html(
        f"""<script>
        const secure = window.parent.location.protocol === "https:" ? "; Secure" : "";
        window.parent.document.cookie =
            "{COOKIE_NAME}={token}; max-age={SESSION_SECONDS}; path=/; SameSite=Lax" + secure;
        </script>""",
        height=0,
    )
    st.success("Signed in!")
    st.page_link("landing.py", label="Continue to Card Shark", icon=":material/home:")
    st.stop()


# If already logged in, show the account and a logout button.

if st.session_state.get("user_id"):
    st.success(f"You are signed in as **{st.session_state.get('username', 'user')}**.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Go to My Decks", use_container_width=True):
            st.switch_page("inventory.py")
    with col2:
        if st.button("Log out", use_container_width=True):
            token = st.session_state.get("session_token") or st.context.cookies.get(COOKIE_NAME)
            try:
                udb.delete_session(token)
            except (pymongo.errors.PyMongoError, RuntimeError):
                pass
            for key in ("user_id", "username", "deck", "session_token"):
                st.session_state.pop(key, None)
            st.rerun()
    st.stop()

tab_login, tab_register = st.tabs(["Log In", "Register"])

# LOG IN

with tab_login:
    with st.form("login_form"):
        login_email = st.text_input("Email")
        login_password = st.text_input("Password", type="password")
        login_submit = st.form_submit_button("Log In", use_container_width=True)

    if login_submit:
        try:
            user = users.authenticate_user(login_email, login_password)
        except (pymongo.errors.PyMongoError, RuntimeError) as error:
            st.error(f"Could not log in: {error}")
        else:
            if user is None:
                st.error("Incorrect email or password.")
            else:
                _finish_login(_sign_in(user))

# REGISTER

with tab_register:
    with st.form("register_form"):
        reg_username = st.text_input("Username", help="3-30 characters: letters, numbers, _ . -")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input(
            "Password",
            type="password",
            key="reg_password",
            help=f"At least {users.MIN_PASSWORD_LENGTH} characters.",
        )
        reg_confirm = st.text_input("Confirm password", type="password")
        reg_submit = st.form_submit_button("Create Account", use_container_width=True)

    if reg_submit:
        if reg_password != reg_confirm:
            st.error("The passwords do not match.")
        else:
            try:
                user = users.create_user(reg_username, reg_email, reg_password)
            except ValueError as error:
                st.error(str(error))
            except (pymongo.errors.PyMongoError, RuntimeError) as error:
                st.error(f"Could not create the account: {error}")
            else:
                _finish_login(_sign_in(user))