import streamlit as st


# Creates the main title "Card Shark"
st.image("logo.png")


# This displays the text underneath Card Shark
st.markdown(
    """<h3 style="text-align: center; font-size: 22px"> A deck builder for Magic: The Gathering </h3>""",
    unsafe_allow_html = True
)


# This displays the horizonatal category selection above the search box
search_type = st.segmented_control(
    "Search by",
    ["Cards", "Decks", "Users"],
    default = "Cards",
    selection_mode = "single"
)


# This part displays the search bar but doesn't do any searching 
# since there's no search logic to search the database yet.
query = st.text_input(
    "",
    placeholder = f"Search {search_type.lower()}...",
    label_visibility = "collapsed"
)


if query:
    # Searching logic goes here...
    # So on user search, it would search for the item(s) matching the user's input and selected category from database
    # I added 'pass' so there is no error when the code is ran, but it WILL get replaced when the real logic is implemented
    pass


# This adds that arrow at the bottom middle of the page, indicating the user there's more below on the landing page
st.markdown("""
<style>
.scroll-down {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 999;
    text-decoration: none !important;
    color: inherit !important;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 10px;
}

.scroll-down span {
    display: block;
    width: 16px;
    height: 16px;
    border-right: 3px solid currentColor;
    border-bottom: 3px solid currentColor;
    transform: rotate(45deg);
    animation: drift 1.8s ease-in-out infinite;
}

.scroll-down span:nth-child(2) {
    animation-delay: 0.3s;
}

@keyframes drift {
    0% {
        opacity: 0;
        transform: translateY(-5px) rotate(45deg);
    }
    50% {
        opacity: 1;
    }
    100% {
        opacity: 0;
        transform: translateY(5px) rotate(45deg);
    }
}
</style>

<a class="scroll-down" href="#shortcuts">
    <span></span>
    <span></span>
</a>
""", unsafe_allow_html=True)


# The code below creates that grid of shortcuts to navigate to the main features of our app.
st.divider()

st.markdown(
    "<h1 style='text-align: center; font-size: 50px;'>Jump right into Card Shark!</h1>",
    unsafe_allow_html = True
)


# Styles the shortcut cards to keep their size consistent; will add color later on
st.markdown("""
<style>
.shortcut-box {
    height: 210px;
    border: 1px solid rgba(128, 128, 128, 0.35);
    border-radius: 12px;
    padding: 18px 12px;
    margin-bottom: 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    box-sizing: border-box;
}
.shortcut-icon {
    font-size: 32px;
    margin-bottom: 8px;
}
.shortcut-title {
    font-size: 19px;
    font-weight: 600;
    margin-bottom: 6px;
}
.shortcut-description {
    font-size: 14px;
    opacity: 0.8;
    min-height: 36px;
}
</style>
""", unsafe_allow_html = True)


# This helps make the 2x2 grid for the shortcuts
col1, col2 = st.columns(2)

# Makes the left column
with col1:
    with st.container(border = True):
        st.markdown("### Build a Deck")
        st.caption("Create a new Magic Deck.")
        if st.button("Open Deck Builder", key = "shortcut_builder", use_container_width = True):
            st.switch_page("app.py")

    with st.container(border=True):
        st.markdown("### Game Rules")
        st.caption("Look up Magic rules.")
        if st.button("Read Rules", key = "shortcut_rules", use_container_width = True):
            st.switch_page("rules.py")

# Makes the right column
with col2:
    with st.container(border = True):
        st.markdown("### My Decks")
        st.caption("View and manage saved decks.")
        if st.button("View My Decks", key = "shortcut_inventory", use_container_width = True):
            st.switch_page("inventory.py")

    with st.container(border = True):
        st.markdown("### Beginner's Guide")
        st.caption("Learn the basics of MTG and deck building.")
        if st.button("Get Started", key = "shortcut_beginner", use_container_width = True):
            st.switch_page("beginner.py")


# This section displays the heading and description at the bottom of the landing page.
st.divider()

st.markdown(
    """
    <div style = "text-align: center;">
        <h1>Ready to Build Your Deck?</h1>
        <p style = "font-size: 18px;">
            Explore Magic cards, build your decks, and keep everything
            organized in one place with Card Shark.
        </p>
    </div>
    """,
    unsafe_allow_html = True
)


# This section displays the Register button and the Log In link for existing users.
# Both are placeholders until the registration and login functionality is implemented.
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button("Register Now", use_container_width = True):
        st.info("Registration page is going to be implemented sometime soon.")

st.markdown(
    "<p style = 'text-align: center; font-size: 13px; margin-top: 8px;'>"
    "Already have an account? "
    "<a href = '#' style = 'text-decoration: underline;'>Log In</a>"
    "</p>",
    unsafe_allow_html = True
)