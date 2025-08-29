import streamlit as st
import pandas as pd
import random
import os

# Function to calculate points based on guess accuracy
def calculate_points(guess, actual):
    if guess == actual:
        return 5
    elif abs(guess - actual) <= 1:
        return 3
    elif abs(guess - actual) <= 2:
        return 2
    elif abs(guess - actual) <= 3:
        return 1
    else:
        return 0

# Load the data with caching
@st.cache_data
def load_data():
    return pd.read_csv('2025_homeruns_running.csv')

# Function to select a new batter
def select_new_batter():
    available_homeruns = df_combined[~df_combined['Name'].isin(st.session_state.used_pitchers)]
    if available_homeruns.empty:
        st.session_state.game_over = True  # Set game over if no pitchers are available
        return None
    random_batter = available_homeruns.sample().iloc[0]
    st.session_state.used_batters.add(random_batter['Name'])
    st.session_state.current_batter = random_batter

# Function to reset the game
def reset_game():
    st.session_state.total_points = 0
    st.session_state.round_num = 1
    st.session_state.used_batters = set()
    st.session_state.feedback_statements = []
    st.session_state.current_batter = None
    st.session_state.game_over = False

# Load data
df_combined = load_data()

# Initialize session state variables
if "total_points" not in st.session_state:
    st.session_state.total_points = 0
    st.session_state.round_num = 1
    st.session_state.used_batters = set()
    st.session_state.feedback_statements = []
    st.session_state.current_batter = None
    st.session_state.game_over = False

rounds = 10  # Total number of rounds in the game

# Main game logic
if st.session_state.round_num > rounds or st.session_state.game_over:
    st.subheader("Game Summary")
    for statement in st.session_state.feedback_statements:
        st.write(statement)
    st.write(f"**Total Points: {st.session_state.total_points}**")
    
    if st.button("Play Again"):
        reset_game()
        select_new_pitcher()
    st.stop()

# If no current batter is selected, select one
if st.session_state.current_batter is None:
    select_new_batter()

# Get current pitcher details
batter = st.session_state.current_batter
batter_name = batter['Name']
launch_speed = batter['EV (MPH)']
total_distance = batter['Dist (ft)]
launch_angle = batter['LA (deg)']
parks_30 = batter['X/30']                        

video_url = batter['video_url']

# Display the batter's name and video
st.subheader(f"Round {st.session_state.round_num}/{rounds} - Batter: {batter_name}")
if os.path.exists(homerun_video_url) and homerun_video_url != 'Not Found':
    st.video(homerun_video_url)
else:
    st.write(f"No video found for {batter_name}.")

# User input for guessing
with st.form(key=f"guess_form_{st.session_state.round_num}"):
    user_guess = st.text_input("Guess the number of parks this would be a homerun in (integer 1-30)", key=f"guess_input_{st.session_state.round_num}")
    submit_button = st.form_submit_button("Submit Guess")

# Process the guess
if submit_button:
    try:
        # Ensure valid format with no decimal poiint
        if  (user_guess and user_guess.count('.') == 1 and len(user_guess.split('.')[-1]) == 1):
            raise ValueError("Invalid format")
        
        user_guess_float = float(user_guess)  # Convert to float

        # Calculate points for the guess
        points = calculate_points(user_guess_float, parks_30)
        st.session_state.total_points += points

        # Store and display feedback for the current (just completed) round
        feedback = (
            f"Round {st.session_state.round_num}/{rounds} - Batter: {batter_name} - "
            f"Your Guess: {user_guess_float}, Actual X/30: {parks_30}, Distance: {total_distance}, Launch Angle: {launch_angle}, Exit Velocity: {launch_speed},  Points Awarded: {points}"
        )
        st.session_state.feedback_statements.append(feedback)
        st.success(feedback)

        # Increment the round number after processing the guess
        st.session_state.round_num += 1

        # Clear current_pitcher to select a new one in the next iteration
        st.session_state.current_pitcher = None

        # Force a rerun to update the UI with the new round
        st.rerun()

    except ValueError:
        st.error("Invalid input. Please enter a speed like '90.0' with exactly one decimal place.")

# Display all feedback statements from previous rounds
if st.session_state.feedback_statements:
    st.subheader("Feedback So Far:")
    for statement in st.session_state.feedback_statements:
        st.write(statement)
