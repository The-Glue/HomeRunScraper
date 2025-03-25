import streamlit as st
import pandas as pd
import random

# Load data
@st.cache_data
def load_data():
    return pd.read_csv("2024_homeruns_updated.csv") 

df = load_data()

# Initialize session state
if "round" not in st.session_state:
    st.session_state.round = 0
    st.session_state.score = 0
    st.session_state.history = []

# Game logic
if st.session_state.round < 10:
    st.subheader(f"Round {st.session_state.round + 1}/10")

    # Randomly select a home run
    row = df.sample(1).iloc[0]
    player_name = " ".join(row["title"].split()[:2])  # Extract name
    hr_number = row["title"].split("(")[1].split(")")[0]  # Extract HR number
    video_url = row["video"]
    actual_x30 = int(row["x/30 ballparks"])

    st.video(video_url)    st.write(f"**{player_name} homers ({hr_number})**")

    guess = st.number_input("Guess how many parks this was a HR in (0-30):", min_value=0, max_value=30, step=1)

    if st.button("Submit Guess"):
        # Scoring logic
        diff = abs(guess - actual_x30)
        if diff == 0:
            points = 10
        elif diff == 1:
            points = 8
        elif diff == 2:
            points = 6
        elif diff == 3:
            points = 4
        elif diff == 4:
            points = 2
        else:
            points = 0

        # Update session state
        st.session_state.round += 1
        st.session_state.score += points
        st.session_state.history.append({
            "Player": player_name,
            "HR #": hr_number,
            "Exit Velo": row["exit_velocity"],
            "Distance": row["distance_projected"],
            "Your Guess": guess,
            "Actual": actual_x30,
            "Points": points
        })

        st.experimental_rerun()

# Display history
if st.session_state.history:
    st.subheader("Game History")
    st.dataframe(pd.DataFrame(st.session_state.history))

# End game screen
if st.session_state.round >= 10:
    st.subheader(f"Game Over! Total Score: {st.session_state.score}")
    if st.button("Restart Game"):
        st.session_state.round = 0
        st.session_state.score = 0
        st.session_state.history = []
        st.experimental_rerun()
