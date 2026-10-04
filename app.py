import streamlit as st

#rocky include
#database include


st.title("MTG Deck Builder")

st.write("Create a Magic: The Gathering deck using Rocky.")


colors = st.text_input("Colors")

format = st.selectbox(
    "Format",
    ["Standard", "Modern", "Commander", "Pioneer", "Legacy", "Vintage"]
)

strategy = st.text_area(
    "What kind of deck do you want?",
    placeholder="Example: Aggressive artifact deck with lots of card draw"
)

if st.button("Generate Deck"):

    if not colors:
        st.warning("Please enter deck colors")
    if not strategy:
        st.warning("Please enter a deck strategy")
    else:
        with st.spinner("Generating deck..."):

            #rocky call to generate deck
            

            st.subheader("Generated Deck")

            st.write(deck)

            if st.button("Save Deck"):
                #database stuff
                st.success("Deck saved!")