import streamlit as st

# Creates the main title "Card Shark"
st.markdown( 
    """<h1 style="text-align: center; letter-spacing: 10px; font-size: 60px"> CARD SHARK </h1>""",
    unsafe_allow_html=True
)

# This displays the text underneath Card Shark
st.markdown(
    """<h3 style="text-align: center; font-size: 20px"> A deck builder for Magic: The Gathering </h3>""",
    unsafe_allow_html=True
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
