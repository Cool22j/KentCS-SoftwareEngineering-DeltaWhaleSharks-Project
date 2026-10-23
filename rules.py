import streamlit as st

st.set_page_config(page_title="Card Shark - MTG Rules", page_icon=":material/menu_book:", layout="wide")

st.markdown(
    """
    <div style="background-color: #1e1e2e; padding: 24px; border-radius: 12px; margin-bottom: 24px;">
        <h1 style="color: #ffffff; margin: 0;">Magic: The Gathering Basic Rules Guide</h1>
        <p style="color: #cbd5e1; font-size: 16px; margin-top: 6px; margin-bottom: 0;">
            A quick reference for turn phases, combat steps, format deck-construction limits, and common keywords.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_turn, tab_combat, tab_formats, tab_stack = st.tabs([
    "1. Turn Phases",
    "2. Combat Breakdown",
    "3. Format Rules",
    "4. The Stack & Priority",
])

# -------------------------------------------------------------
# TAB 1: TURN PHASES
# -------------------------------------------------------------
with tab_turn:
    st.subheader("The Five Phases of a Turn")
    st.write("A standard turn in Magic proceeds through five mandatory phases in strict sequential order.")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("#### 1. Beginning Phase")
            st.markdown(
                """
                - **Untap Step:** Untap all of your tapped permanents (Lands, Creatures, Artifacts). No player receives priority to cast spells or activate abilities here.
                - **Upkeep Step:** Any triggered abilities specifying *"at the beginning of your upkeep"* go onto the stack. Players may cast Instants and activate abilities.
                - **Draw Step:** The active player draws the top card of their library. (Note: The player going first in a 1v1 game skips their draw step on turn 1).
                """
            )

        with st.container(border=True):
            st.markdown("#### 2. Pre-Combat Main Phase")
            st.markdown(
                """
                - You may play **one Land** per turn (unless cards grant additional land drops). Playing a land does not use the stack and cannot be countered.
                - Cast Sorceries, Creatures, Artifacts, Enchantments, Planeswalkers, and Instants.
                - Activate permanent abilities.
                """
            )
        
        with st.container(border=True):
            st.markdown("#### 3. Combat Phase")
            st.markdown(
                """
                - If you wish to attack with untapped creatures that do not have summoning sickness, you enter combat.
                - Includes: Beginning of Combat, Declare Attackers, Declare Blockers, Combat Damage, and End of Combat.
                """
            )

        with st.container(border=True):
            st.markdown("#### 4. Post-Combat Main Phase")
            st.markdown(
                """
                - Exactly identical to the first main phase.
                - You may play your land for the turn here if you did not play one during the pre-combat main phase.
                - A great strategic window to cast creatures and sorceries after seeing how combat resolved.
                """
            )

        with st.container(border=True):
            st.markdown("#### 5. Ending Phase")
            st.markdown(
                """
                - **End Step:** Triggered abilities stating *"at the beginning of the end step"* resolve. Players have a final opportunity to cast Instants.
                - **Cleanup Step:** Active player discards down to maximum hand size (usually 7). All marked damage on creatures is removed, and *"until end of turn"* effects expire.
                """
            )

        #with col2:
            #immage placeholder for a turn phases diagram

# -------------------------------------------------------------
# TAB 2: COMBAT BREAKDOWN
# -------------------------------------------------------------
with tab_combat:
    st.subheader("Combat Phase Step-by-Step")

    c_steps = [
        ("Step 1: Beginning of Combat", "Active player announces intent to enter combat. Opponents have priority to cast instants or activate abilities (e.g., tapping down an opponent's creature before it can attack)."),
        ("Step 2: Declare Attackers", "Active player chooses which untapped creatures are attacking and which player (or planeswalker) they are attacking. Taps attackers (unless they have Vigilance). Once declared, priority passes to players."),
        ("Step 3: Declare Blockers", "Defending player designates which untapped creatures will block which attacking creatures. Multiple creatures may block a single attacker. The attacking player orders multiple blockers for damage assignment."),
        ("Step 4: Combat Damage","Creatures deal damage equal to their Power. If any creature has First Strike or Double Strike, an extra preliminary damage step occurs prior to regular damage. Lethal damage destroys creatures immediately as a state-based action."),
        ("Step 5: End of Combat", "'At end of combat' triggers resolve. All surviving creatures remain in play, and the game moves to the Post-Combat Main Phase."),
    ]

    for title, desc in c_steps:
        with st.expander(title, expanded=False):
            st.write(desc)

# -------------------------------------------------------------
# TAB 3: FORMAT RULES
# -------------------------------------------------------------
with tab_formats:
    st.subheader("Deck Construction Formats")
    st.write("Compare the restrictions between popular tabletop and digital formats.")

    col_fmt1, col_fmt2 = st.columns(2)

    with col_fmt1:
        with st.container(border=True):
            st.markdown("### Standard")
            st.markdown(
                """
                - **Deck Size:** Minimum 60 cards (no maximum limit, but must be shuffleable).
                - **Sideboard:** Up to 15 cards.
                - **Copy Limit:** Up to 4 copies of any unique card (unlimited Basic Lands).
                - **Starting Life:** 20.
                - **Card Pool:** Rotating sets released within the last 3 years.
                """
            )

        with st.container(border=True):
            st.markdown("### Modern")
            st.markdown(
                """
                - **Deck Size:** Minimum 60 cards.
                - **Sideboard:** Up to 15 cards.
                - **Copy Limit:** Up to 4 copies of any unique card.
                - **Starting Life:** 20.
                - **Card Pool:** Non-rotating format featuring sets printed from *Eighth Edition* (2003) to the present, plus direct-to-modern Modern Horizons sets (subject to the Modern Banned List).
                """
            )

    with col_fmt2:
        with st.container(border=True):
            st.markdown("### Commander (EDH)")
            st.markdown(
                """
                - **Deck Size:** Exactly 100 cards (1 Commander + 99 main deck cards).
                - **Commander:** A Legendary Creature (or specific Planeswalker) placed in the Command Zone.
                - **Copy Limit:** **Singleton format** (exactly 1 copy of any card, except Basic Lands).
                - **Color Identity:** No card in the 99 may feature colored mana symbols outside your Commander's color identity.
                - **Starting Life:** 40 (typically played as a 4-player free-for-all).
                - **Commander Damage Rule:** A player who takes 21 combat damage from a single Commander loses the game.
                """
            )

        with st.container(border=True):
            st.markdown("### Pioneer & Pauper")
            st.markdown(
                """
                - **Pioneer:** 60-card minimum using sets from *Return to Ravnica* (2012) forward.
                - **Pauper:** 60-card minimum where every included card must have been printed at **Common** rarity in any Magic set.
                """
            )


# -------------------------------------------------------------
# TAB 4: THE STACK & PRIORITY
# -------------------------------------------------------------
with tab_stack:
    st.subheader("The Stack: Last In, First Out (LIFO)")
    st.markdown(
        """
        The **Stack** is the zone where spells and abilities wait to resolve. Understanding the stack is crucial for timing and counter-play.
        
        1. **Casting a Spell:** When you cast a spell or activate an ability, it is placed on top of the stack. Mana costs are paid immediately.
        2. **Passing Priority:** Before the spell resolves, priority passes to your opponent. They may respond by adding another Instant or activated ability on top of your spell.
        3. **Resolution:** When all players pass priority without adding new spells, the top item of the stack resolves. 
        4. **Order:** The most recently added spell always resolves **first** (*Last In, First Out*).
        """
    )

    st.markdown("#### Example Stack Resolution")
    st.code(
        """
Top of Stack (Resolves 1st): [Player B] Counterspell (Targeting Lightning Bolt)
Bottom of Stack (Resolves 2nd): [Player A] Lightning Bolt (Targeting Player B)

Result: Counterspell resolves, countering Lightning Bolt. Lightning Bolt goes to the graveyard without dealing damage.
        """,
        language="text"
    )

st.divider()
if st.button("Ready to build? Go to the Deck Builder", type="primary"):
    st.switch_page("app.py")