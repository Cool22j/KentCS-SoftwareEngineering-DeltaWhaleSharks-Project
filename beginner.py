import streamlit as st

# Creates the title of the page
st.markdown(
    "<h1 style='text-align: center; font-size: 40px;'>"
    "Beginner's Guide to Magic: The Gathering"
    "</h1>",
    unsafe_allow_html = True
)

st.divider()

# This displays the text giving the brief overview of what the guide will contain
st.markdown(
    "<h4 style='text-align: center; font-size: 20px;'>"
    "Welcome to the Beginner's Guide to Magic: The Gathering (MTG)! " 
    "This guide will teach you the basics of the game, explain how different cards work, " 
    "and help you learn how to build your own deck."
    "</h4>",
    unsafe_allow_html = True
)

st.divider()

# This sections lays out how a regular game of MTG would play out..
st.header("How a Typical Game Works")

st.write(
    """
    Magic: The Gathering is a card game where players use their own
    decks to battle each other. You play cards, use resources to pay
    for them, and make decisions to try to defeat your opponent.
    """
)

with st.expander("Starting the Game"):
    st.markdown(
        """
        - **Shuffle your deck:** Mix your cards so they are in a
          random order.

        - **Draw your opening hand:** Each player draws seven cards
          to start the game.

        - **Choose whether to keep your hand:** If you don't like
          your starting cards, you can take a *mulligan*. This means
          shuffling your hand back into your deck and drawing seven
          new cards. Each time you take a mulligan, you must put
          one additional card from your hand on the bottom of your
          deck when you decide to keep your hand.

        - **Get ready to play:** Once everyone has kept their hand,
          the game begins.
        """
    )

with st.expander("Turn Structure"):
    st.markdown(
        """
        Each turn has several parts. During your turn, you can prepare
        your cards, play new cards, and attack your opponent.

        1. **Start of Turn:** Turn your used cards upright so you
           can use them again, handle any effects that happen at
           the start of your turn, and draw a card.

        2. **First Main Phase:** You can play a land, which helps
           you pay for other cards, and play spells such as creatures
           and other useful cards.

        3. **Combat:** Choose which of your creatures will attack.
           Your opponent can use their own creatures to block and
           defend against those attacks.

        4. **Second Main Phase:** You can play more cards and use
           any resources you have left. You can play a land here if
           you haven't already played one this turn.

        5. **End of Turn:** Finish resolving effects that happen
           at the end of your turn and complete any required cleanup.
        """
    )

st.divider()

# This section gives the information on how you can win the game
st.header("How to Win the Game")

st.write(
    """
    The main goal of MTG is to defeat your opponent. There are
    several ways a player can win, depending on the cards being used
    and the rules of the game.
    """
)

with st.expander("Reduce Your Opponent's Life to Zero"):
    st.markdown(
        """
        Most games start with each player having 20 life.
        You can reduce your opponent's life by attacking with
        creatures or using spells that deal damage.

        For example, if your opponent has 5 life and you deal
        5 damage to them, they lose the game.
        """
    )

with st.expander("Make Your Opponent Run Out of Cards"):
    st.markdown(
        """
        Each player has a deck called a **library**. When you draw
        a card, you take the top card from your library and put it
        into your hand.

        If a player must draw a card but has no cards left in their
        library, they lose the game. Some decks use cards that make
        their opponents get rid of cards from their libraries.
        This strategy is called **mill**.
        """
    )

with st.expander("Use Poison Counters"):
    st.markdown(
        """
        Some cards give players **poison counters**. These are
        special counters that track how much poison a player has
        received.

        In the usual rules, a player loses the game when they
        receive 10 or more poison counters. Certain cards are
        designed to win by giving the opponent poison counters
        instead of dealing regular damage.
        """
    )

with st.expander("Win Through Special Card Effects"):
    st.markdown(
        """
        Some cards have special instructions that let you win the
        game when certain conditions are met.

        These conditions vary from card to card, so read the card
        carefully to understand what you need to do to win.
        """
    )

st.divider()

# This part of the guide explains how different MTG formats affect starting life, deck sizes, and the rules players follow when building decks
st.header("Game Mechanics by Format")

st.write(
    """
    MTG can be played in different formats. A format is a set
    of rules that determines how players build their decks and
    play the game. Two popular formats are Standard and Commander.
    """
)

with st.expander("Starting Life Total"):
    st.markdown(
        """
        **Life** represents how close you are to losing the game.
        Most one-on-one games start with each player at 20 life.

        In Commander, each player usually starts with 40 life
        because the format is designed for multiplayer games.
        """
    )

with st.expander("Deck Size"):
    st.markdown(
        """
        The number of cards you need depends on the format.

        - **Standard:** Your deck must contain at least 60 cards.
          There is no maximum deck size, as long as you can shuffle
          your deck without assistance.
        - **Commander:** Your deck contains exactly 100 cards,
          including your commander, which is the special card
          your deck is built around.

        Different formats also have rules about which cards you
        are allowed to use.
        """
    )

with st.expander("Choosing a Format"):
    st.markdown(
        """
        If you're new to MTG, a preconstructed deck is a deck that is 
        already built for you, making it easier to learn the game.
        
        Preconstructed decks are a good way to start playing 
        without having to build your own deck from scratch.
        """
    )

st.divider()

# This explains the main types of cards and what each one does
st.header("Types of Cards")

st.write(
    """
    MTG has several types of cards. Each type serves a different
    purpose, from helping you pay for other cards to attacking
    your opponent or creating special effects.
    """
)

with st.expander("Lands"):
    st.markdown(
        """
        Lands provide **mana**, which is the resource used to pay
        for most cards. You usually play one land per turn.

        Lands are important because you need enough mana to play
        your creatures and other spells.
        """
    )

with st.expander("Creatures"):
    st.markdown(
        """
        Creatures are cards that can usually attack your opponent
        or block attacking creatures.

        Each creature has a **power** and **toughness**. Power tells
        you how much damage it deals in combat, while toughness
        tells you how much damage it can take before it is destroyed.

        For example, a creature with 3 power and 2 toughness can
        deal 3 damage in combat and is normally destroyed if it
        takes 2 or more damage during the same turn.
        """
    )

with st.expander("Instants"):
    st.markdown(
        """
        Instants are spells that can usually be played during
        either player's turn, including in response to another spell
        or action.

        They can do things like deal damage, protect a creature,
        or change what happens during a game.
        """
    )

with st.expander("Sorceries"):
    st.markdown(
        """
        Sorceries are spells that you normally play during one of
        your main phases when the stack is empty.

        They can have effects such as dealing damage, drawing cards,
        or destroying another card.
        """
    )

with st.expander("Artifacts"):
    st.markdown(
        """
        Artifacts are usually objects or pieces of equipment with
        special effects. Some provide useful abilities, while others
        can make your creatures stronger.

        Many artifacts stay on the battlefield after you play them.
        """
    )

with st.expander("Enchantments"):
    st.markdown(
        """
        Enchantments are cards that create ongoing effects.

        Some affect the entire game, while others attach to a
        creature or another card to give it an advantage or
        disadvantage.
        """
    )

with st.expander("Planeswalkers"):
    st.markdown(
        """
        Planeswalkers are powerful cards with special abilities.
        They usually enter the battlefield with loyalty counters,
        which represent their loyalty.

        You can use one of their abilities during your main phase.
        Some abilities add or remove loyalty counters to produce
        different effects.
        """
    )

st.divider()

# Explains mana, card costs, and the five colors of MTG.
st.header("Understanding Mana and the Five Colors")

st.write(
    """
    Most cards require you to pay a cost before you can play them.
    This cost is usually paid with mana, a resource you get mainly
    from lands. Different cards require different amounts or colors
    of mana.
    """
)

with st.expander("Understanding Mana Costs"):
    st.markdown(
        """
        Each card has a mana cost near the top-right corner.
        The symbols show how much mana you need to play that card.

        - **Generic mana:** A number means you can pay that amount
          using mana of any color.
        - **Colored mana:** A colored symbol means you must pay
          mana of that specific color.

        For example, a cost of **3W** requires four mana in total:
        three mana of any color and one white mana.

        Lands usually provide mana when you tap them. Tapping means
        turning a card sideways to show that you have used it.
        """
    )

with st.expander("The Five Colors of MTG"):
    st.markdown(
        """
        MTG has five colors. Each has its own strengths and
        common strategies.

        - **White:** Focuses on teamwork, protection, order,
          and gaining life.
        - **Blue:** Focuses on knowledge, drawing cards, controlling
          the game, and countering spells.
        - **Black:** Focuses on power, sacrifice, using life as
          a resource, and bringing creatures back from the graveyard.
        - **Red:** Focuses on speed, direct damage, and aggressive
          strategies.
        - **Green:** Focuses on powerful creatures, growth, and
          producing extra mana.
        """
    )

with st.expander("Choosing Your Colors"):
    st.markdown(
        """
        Each color has different strengths, so choosing colors
        helps shape how your deck plays.

        For example, red decks often try to deal damage quickly,
        while green decks often use large creatures to overwhelm
        their opponents.

        You can build a deck around one color or combine multiple
        colors to use different strengths together.
        """
    )

st.divider()

# This explains common creature abilities and how they affect gameplay
st.header("Creature Abilities")

st.write(
    """
    Some creatures have special abilities that make them more useful
    in certain situations. These abilities can help creatures attack,
    defend, or deal with other creatures.
    """
)

with st.expander("Flying and Reach"):
    st.markdown(
        """
        - **Flying:** A creature with Flying can only be blocked by
          creatures with Flying or Reach.

        - **Reach:** A creature with Reach can block creatures with
          Flying, even if it does not have Flying itself.

        These abilities can make a big difference when defending
        against creatures that are difficult to block.
        """
    )

with st.expander("Trample and Lifelink"):
    st.markdown(
        """
        - **Trample:** When a creature with Trample attacks and is
          blocked, it can deal extra damage to the defending player
          or planeswalker after assigning enough damage to its blockers.

        - **Lifelink:** When a creature deals damage, its controller
          gains that much life.

        For example, if your creature with Lifelink deals 3 damage,
        you gain 3 life.
        """
    )

with st.expander("Deathtouch and First Strike"):
    st.markdown(
        """
        - **Deathtouch:** Any amount of damage a creature with
          Deathtouch deals to another creature is normally enough
          to destroy it.

        - **First Strike:** A creature with First Strike deals its
          combat damage before creatures without First Strike.

        This can help a creature defeat an opponent's creature
        before it has a chance to deal its own combat damage.
        """
    )

with st.expander("Double Strike and Vigilance"):
    st.markdown(
        """
        - **Double Strike:** A creature deals combat damage twice:
          once during the first-strike damage step and again during
          the regular combat damage step, if it is still able to
          deal damage.

        - **Vigilance:** Attacking with a creature does not cause
          it to tap. This means it can usually still be used to block
          during your opponent's turn.
        """
    )

with st.expander("Haste and Prowess"):
    st.markdown(
        """
        - **Haste:** A creature can attack or use abilities that
          require tapping or untapping even if you have not controlled
          it continuously since the start of your turn.

        - **Prowess:** Whenever you cast a noncreature spell, the
          creature gets +1 power and +1 toughness until the end
          of the turn.

        A noncreature spell is a spell that is not a creature card,
        such as an instant or sorcery.
        """
    )

with st.expander("Sacrificing a Creature"):
    st.markdown(
        """
        **Sacrifice** means choosing one of your permanents and
        putting it into your graveyard. Your graveyard is where
        cards go when they are destroyed, discarded, or otherwise
        removed from the battlefield.

        Some cards let you sacrifice a creature to gain life, deal
        damage, draw cards, or activate another ability.
        """
    )

st.divider()

# Explains common deck strategies to help beginners choose a playstyle.
st.header("Choosing a Playstyle")

st.write(
    """
    A playstyle is the strategy you use to try to win a game.
    Some decks try to defeat opponents quickly, while others focus
    on defending themselves, using powerful combinations of cards,
    or building up resources for stronger plays.
    """
)

with st.expander("Aggro (Aggressive Decks)"):
    st.markdown(
        """
        Aggro decks try to win quickly by attacking early and often.
        They usually use low-cost creatures and spells that deal damage.

        **Example:** Playing several small creatures and attacking
        your opponent before they have time to build a strong defense.
        """
    )

with st.expander("Control (Defensive Decks)"):
    st.markdown(
        """
        Control decks focus on slowing down their opponents.
        They may use spells to stop other spells, remove creatures,
        or draw extra cards to find useful answers.

        **Example:** Stopping an opponent's powerful creature from
        entering the battlefield, then winning later with a stronger card.
        """
    )

with st.expander("Midrange"):
    st.markdown(
        """
        Midrange decks balance early plays with more powerful cards
        later in the game. They try to respond to their opponent's
        strategy while building up their own threats.

        **Example:** Using smaller creatures early, then playing
        larger creatures as the game continues.
        """
    )

with st.expander("Combo"):
    st.markdown(
        """
        Combo decks use two or more cards that work especially well
        together. Some combinations can create a powerful effect or
        even win the game when the right conditions are met.

        **Example:** Combining cards that repeatedly create resources
        or trigger abilities to produce a much bigger effect.
        """
    )

with st.expander("Lifegain"):
    st.markdown(
        """
        Lifegain decks focus on gaining life. Some cards also become
        stronger or create other benefits whenever you gain life.

        **Example:** Gaining life while playing creatures that become
        more powerful as your life total increases.
        """
    )

with st.expander("Ramp"):
    st.markdown(
        """
        Ramp decks try to get access to more mana sooner than usual.
        This lets them play expensive cards earlier in the game.

        **Example:** Using cards that provide extra mana to play a
        powerful creature ahead of schedule.
        """
    )

with st.expander("Other Playstyles"):
    st.markdown(
        """
        There are many other strategies in MTG, including:

        - **Tokens:** Creating extra creatures called tokens.
        - **Mill:** Making an opponent put cards from the top of
          their deck into their graveyard.
        - **Reanimator:** Bringing creatures back from the graveyard
          to use them again.
        - **Tempo:** Gaining an advantage by disrupting an opponent
          while making efficient plays of your own.

        Some decks combine several playstyles instead of relying
        on just one strategy.
        """
    )

st.divider()

# Explains the basics of building a deck for a new MTG player.
st.header("Building Your First Deck")

st.write(
    """
    Once you understand the basics of MTG, you can start building
    a deck. Your deck should include cards that work well together
    and support the strategy you want to use.
    """
)

with st.expander("Starting with a Preconstructed Deck"):
    st.markdown(
        """
        A preconstructed deck is a deck that has already been built
        for you. It lets you start playing without having to choose
        every card yourself.

        Playing with a preconstructed deck can also help you learn
        which cards you enjoy using before building your own deck.
        """
    )

with st.expander("Choosing Cards That Work Together"):
    st.markdown(
        """
        When choosing cards, think about how they support your
        strategy. For example, if your deck focuses on creatures,
        you might include cards that make your creatures stronger
        or help you play more of them.

        Having cards that work together can make your deck more
        consistent and easier to use.
        """
    )

with st.expander("Including Enough Lands"):
    st.markdown(
        """
        Lands provide mana, which you use to pay for most spells.
        If your deck has too few lands, you may struggle to play
        your cards. If it has too many, you may draw fewer spells
        and creatures.

        A typical 60-card deck often starts with around 24 lands,
        but the right number depends on the cards in your deck
        and how much mana they cost.
        """
    )

with st.expander("Understanding the Mana Curve"):
    st.markdown(
        """
        A **mana curve** describes how much your cards cost to play.
        A deck with a good balance of costs gives you useful options
        throughout the game.

        For example, a deck might include:
        - **Low-cost cards** to play early in the game.
        - **Medium-cost cards** to help you build up your strength.
        - **High-cost cards** that can have a big impact later.

        If most of your cards cost a lot of mana, you may struggle
        to do much during the early turns.
        """
    )

with st.expander("Testing and Improving Your Deck"):
    st.markdown(
        """
        After building your deck, play some games to see how it works.

        Pay attention to whether you have enough lands, whether you 
        can play cards early in the game, and whether your cards
        support your strategy.

        You can then replace cards that aren't helping and try
        different combinations to improve your deck.
        """
    )

st.divider()

# Defines common MTG terms that beginners may encounter while playing.
st.header("Common MTG Terms")

st.write(
    """
    MTG players use certain words to describe cards, actions,
    and strategies. Learning these terms will make it easier to
    understand the game and communicate with other players.
    """
)

with st.expander("Game Terms"):
    st.markdown(
        """
        - **Topdeck:** Drawing a card from your library, especially
          when you need a useful card to help you win.

        - **Mulligan:** Choosing to replace your starting hand
          before the game begins.

        - **Token:** A marker representing a creature or other
          permanent created by a card's effect.

        - **Graveyard:** The pile where cards go after being
          destroyed, discarded, or otherwise put there.

        - **Scoop:** Informal slang for conceding, which means
          choosing to give up and end your game.
        """
    )

with st.expander("Deck and Strategy Terms"):
    st.markdown(
        """
        - **Aggro:** A strategy that tries to defeat opponents quickly.

        - **Control:** A strategy focused on slowing down opponents
          and managing their threats.

        - **Combo:** A strategy that uses cards together to create
          a powerful effect.

        - **Burn:** A strategy that uses damage-dealing spells to
          reduce an opponent's life total.

        - **Mill:** Making an opponent put cards from their library
          into their graveyard.

        - **Ramp:** Getting access to additional mana sooner than usual.

        - **Sideboard:** A separate group of cards that can be
          swapped into a deck between games in formats that allow it.
        """
    )

with st.expander("Other Useful Terms"):
    st.markdown(
        """
        - **Tilt:** Feeling frustrated after a bad play or loss,
          which can make it harder to make good decisions.

        - **Reanimator:** A strategy focused on bringing creatures
          back from the graveyard.

        - **Mana curve:** The distribution of card costs in a deck.

        - **Aggro-control:** A strategy that combines aggressive
          attacks with ways to disrupt an opponent.
        """
    )

st.divider()

# Gives beginners advice for improving their MTG skills.
st.header("Improving at MTG")

st.write(
    """
    Learning MTG takes practice. You don't need to understand
    every rule or strategy right away. Playing games and learning
    from your experiences will help you improve over time.
    """
)

with st.expander("Practice Regularly"):
    st.markdown(
        """
        Playing regularly helps you become familiar with the rules,
        learn how different cards work, and recognize common situations.

        Try different decks and strategies to discover what you enjoy
        and understand how other players approach the game.
        """
    )

with st.expander("Learn from Your Games"):
    st.markdown(
        """
        After a game, think about what went well and what you could
        do differently next time.

        For example, consider whether you played your lands at the
        right time, used your spells effectively, or kept cards that
        didn't help your strategy.

        Losing a game can still teach you something useful.
        """
    )

with st.expander("Read Your Cards Carefully"):
    st.markdown(
        """
        Take time to read your cards and understand what they do.
        Pay attention to their costs, abilities, and instructions.

        If you're unsure about a rule, look it up or ask a more
        experienced player. Understanding how your cards work can
        help you make better decisions during a game.
        """
    )

with st.expander("Learn from Other Players"):
    st.markdown(
        """
        Playing with other people gives you opportunities to learn
        new strategies and see cards used in different ways.

        You can ask questions, discuss interesting plays, and learn
        from players with more experience. Most importantly, enjoy
        the process of learning and improving.
        """
    )

st.divider()

# Provides a closing section that directs users to the deck builder to apply what they learned and explore cards in Card Shark
st.header("Continue Exploring MTG")

st.write(
    """
    Ready to put what you've learned into practice? Head over to
    the Deck Builder to start creating your own deck and explore
    the cards available in Card Shark.
    """
)

if st.button("Open Deck Builder", use_container_width=True):
    st.switch_page("app.py")