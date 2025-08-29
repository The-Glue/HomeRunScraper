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

# --- MODIFIED: Function to select a new batter with a valid video URL ---
def select_new_batter():
    # Use a loop to find a homerun with a valid video
    max_attempts = 50 # Prevent infinite loops in case of no valid videos
    for _ in range(max_attempts):
        # Filter out batters already used and get a random sample
        available_homeruns = df_combined[~df_combined['Name'].isin(st.session_state.used_batters)]
        if available_homeruns.empty:
            st.session_state.game_over = True
            return None

        # Select a random homerun
        random_batter = available_homeruns.sample().iloc[0]
        video_url = random_batter.get('video_url')

        # Check if a video URL exists and is not 'Not Found'
        if pd.notna(video_url) and video_url != 'Not Found' and video_url.strip() != '':
            # Found a valid homerun, store it in session state and exit the loop
            st.session_state.used_batters.add(random_batter['Name'])
            st.session_state.current_batter = random_batter
            return
    
    # If the loop finishes without finding a valid video, end the game
    st.session_state.game_over = True
    st.error("No available home runs with valid videos found to continue the game.")


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
    reset_game()

rounds = 10  # Total number of rounds in the game

# Main game logic
if st.session_state.round_num > rounds or st.session_state.game_over:
    st.subheader("Game Summary")
    for statement in st.session_state.feedback_statements:
        st.write(statement)
    st.write(f"**Total Points: {st.session_state.total_points}**")
    
    if st.button("Play Again"):
        reset_game()
        select_new_batter() # FIX: Corrected function name
        st.experimental_rerun()
    st.stop()

# If no current batter is selected, select one
if st.session_state.current_batter is None:
    select_new_batter()
    # Rerun if a batter was found to proceed with the round
    if st.session_state.current_batter is not None:
        st.experimental_rerun()

# Check for game over state after attempting to select a new batter
if st.session_state.game_over:
    st.subheader("Game Summary")
    for statement in st.session_state.feedback_statements:
        st.write(statement)
    st.write(f"**Total Points: {st.session_state.total_points}**")
    st.error("Game Over: No more home runs with valid videos are available.")
    if st.button("Play Again"):
        reset_game()
        select_new_batter()
    st.stop()

# Get current batter details
batter = st.session_state.current_batter
batter_name = batter['Name']
launch_speed = batter['EV (MPH)']
total_distance = batter['Dist (ft)'] # FIX: Corrected 'Dist (ft)]' to 'Dist (ft)'
launch_angle = batter['LA (deg)']
parks_30 = batter['X/30']
video_url = batter['video_url'] # FIX: Ensure we're using the correct column name

# Display the batter's name and video
st.subheader(f"Round {st.session_state.round_num}/{rounds} - Batter: {batter_name}")
st.video(video_url)

# User input for guessing
with st.form(key=f"guess_form_{st.session_state.round_num}"):
    user_guess_str = st.text_input("Guess the number of parks this would be a homerun in (integer 1-30)", key=f"guess_input_{st.session_state.round_num}")
    submit_button = st.form_submit_button("Submit Guess")

# Process the guess
if submit_button:
    try:
        # FIX: Corrected validation logic. Check if the input is a valid integer.
        if user_guess_str.strip() == '':
            raise ValueError("Input cannot be empty.")
        user_guess_int = int(user_guess_str)
        if not (1 <= user_guess_int <= 30):
            raise ValueError("Guess must be between 1 and 30.")

        # Calculate points for the guess
        points = calculate_points(user_guess_int, parks_30)
        st.session_state.total_points += points

        # Store and display feedback for the current (just completed) round
        feedback = (
            f"Round {st.session_state.round_num}/{rounds} - Batter: {batter_name} - "
            f"Your Guess: {user_guess_int}, Actual X/30: {parks_30}, Distance: {total_distance}, Launch Angle: {launch_angle}, Exit Velocity: {launch_speed},  Points Awarded: {points}"
        )
        st.session_state.feedback_statements.append(feedback)
        st.success(feedback)

        # Increment the round number after processing the guess
        st.session_state.round_num += 1

        # Clear current_batter to select a new one in the next iteration
        st.session_state.current_batter = None

        # Force a rerun to update the UI with the new round
        st.experimental_rerun()

    except ValueError as e:
        st.error(f"Invalid input: {e}")

# Display all feedback statements from previous rounds
if st.session_state.feedback_statements:
    st.subheader("Feedback So Far:")
    for statement in st.session_state.feedback_statements:
        st.write(statement)
