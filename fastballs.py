import pandas as pd
import json
import requests
import time
import csv
import os # This module helps check if files exist

# --- Configuration ---
output_csv_filename = 'fastballs_2025.csv'
schedule_filename = 'mlb_schedule_2025.csv' # IMPORTANT: Ensure this file is updated periodically
                                         # with the full season's schedule, including past and future games.

csv_headers = [
    'gamePk',
    'gameDate',
    'playId',
    'pitchNum',
    'pitcherId',
    'pitcherName',
    'batterId',
    'batterName',
    'pitchSpeed',
    'spinRate',
    'pitchTypeDescription',
    'pitchTypeCode'
]

fastball_codes = ['FA', 'FF', 'FT', 'FC', 'SI']

# --- Function to get already processed game Pks ---
def get_processed_game_pks(filename):
    """
    Reads the output CSV and returns a set of gamePks that have already been processed.
    This set is used to avoid reprocessing games.
    """
    processed_pks = set()
    
    # Check if the output file exists and has content
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        try:
            # Read only the 'gamePk' column for efficiency, skipping header row if it exists
            # error_bad_lines=False handles potential malformed rows gracefully
            df = pd.read_csv(filename, usecols=['gamePk'], dtype={'gamePk': int})
            processed_pks.update(df['gamePk'].unique())
            print(f"Found {len(processed_pks)} unique gamePks already collected in '{filename}'.")
        except pd.errors.EmptyDataError:
            print(f"'{filename}' exists but is empty. Will start data collection fresh.")
        except KeyError:
            print(f"Warning: '{filename}' exists but 'gamePk' column not found. It might be malformed.")
        except Exception as e:
            print(f"Warning: Could not read existing data from '{filename}' for filtering: {e}")
            # If there's an error reading, we'll proceed as if no games were processed.
            # This might lead to re-processing but ensures no data is missed.
    else:
        print(f"'{filename}' not found or is empty. Will start data collection fresh.")
    return processed_pks

# --- Main Logic ---
try:
    # 1. Identify which games have already been successfully processed
    already_processed_game_pks = get_processed_game_pks(output_csv_filename)

    # Determine if headers need to be written.
    # Headers are only written if the output CSV file is brand new or completely empty.
    write_headers = not os.path.exists(output_csv_filename) or os.path.getsize(output_csv_filename) == 0

    # Open the output CSV file in 'append' mode ('a').
    # If the file doesn't exist, Python will create it automatically.
    with open(output_csv_filename, 'a', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        
        # Write headers only if required (i.e., this is the first time data is being written)
        if write_headers:
            writer.writerow(csv_headers)
            print("CSV headers written to new/empty file.")

        # 2. Load the entire MLB schedule
        try:
            full_schedule = pd.read_csv(schedule_filename)
            # It's good practice to ensure 'gamePk' is treated as integer for consistent comparison
            full_schedule['gamePk'] = full_schedule['gamePk'].astype(int) 
        except FileNotFoundError:
            print(f"Error: Schedule file '{schedule_filename}' not found. Please ensure it exists.")
            exit() # Cannot proceed without the schedule file
        except Exception as e:
            print(f"Error reading schedule file '{schedule_filename}': {e}")
            exit()

        # 3. Filter the schedule to find only the games that need to be processed
        # These are games that are NOT in our 'already_processed_game_pks' set.
        games_to_process = []
        for index, row in full_schedule.iterrows():
            game_pk = row['gamePk']
            if game_pk not in already_processed_game_pks:
                games_to_process.append({'gamePk': game_pk, 'gameDate': row['date']})

        if not games_to_process:
            print("No new or previously missed games to process. All available games in the schedule are already collected.")
            exit() # Exit if there's nothing to do

        print(f"Found {len(games_to_process)} new or previously missed games to process.")
        
        # 4. Iterate and process only the filtered games
        for game_info in games_to_process:
            game_pk = game_info['gamePk']
            game_date = game_info['gameDate']

            url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
            
            print(f"Attempting to fetch data for game_pk: {game_pk} on {game_date}")
            
            try:
                # Fetch data from the MLB API
                response = requests.get(url, timeout=10) # Keep timeout for network robustness
                response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
                game_data = response.json()

                all_plays = game_data.get('liveData', {}).get('plays', {}).get('allPlays', [])
                
                # Extract player information and iterate through play events (pitches)
                for play_index, play in enumerate(all_plays):
                    batter_data = play.get('matchup', {}).get('batter', {})
                    batter_id = batter_data.get('id')
                    batter_name = batter_data.get('fullName')
                    
                    pitcher_data = play.get('matchup', {}).get('pitcher', {})
                    pitcher_id = pitcher_data.get('id')
                    pitcher_name = pitcher_data.get('fullName')

                    play_events = play.get('playEvents', [])
                    
                    for event_num, event in enumerate(play_events):
                        pitch_data = event.get('pitchData')
                        
                        # Only process if it's a pitch event with details
                        if pitch_data and event.get('details'):
                            details = event.get('details')
                            pitch_type_obj = details.get('type')

                            pitch_type_description = None
                            pitch_type_code = None

                            if isinstance(pitch_type_obj, dict):
                                pitch_type_description = pitch_type_obj.get('description')
                                pitch_type_code = pitch_type_obj.get('code')

                            # Check if the pitch is a fastball type
                            if pitch_type_code in fastball_codes:
                                # Get playId directly from the event object for granular linkage
                                play_id_for_this_pitch = event.get('playId') 
                                
                                pitch_speed = pitch_data.get('startSpeed')
                                spin_rate = pitch_data.get('breaks', {}).get('spinRate')
                                
                                # Prepare the row data
                                fastball_data_row = [
                                    game_pk,
                                    game_date,
                                    play_id_for_this_pitch,
                                    event_num,
                                    pitcher_id,
                                    pitcher_name,
                                    batter_id,
                                    batter_name,
                                    pitch_speed,
                                    spin_rate,
                                    pitch_type_description,
                                    pitch_type_code
                                ]
                                
                                # Write the row to the CSV file
                                writer.writerow(fastball_data_row)
                
                # IMPORTANT: After successfully processing all plays for a game,
                # add its gamePk to the set of processed games. This ensures that
                # if the script is interrupted after a game is fully processed,
                # it won't be re-fetched in the next run.
                already_processed_game_pks.add(game_pk)

            except requests.exceptions.RequestException as e:
                print(f"  Error fetching data for {game_pk}: {e}")
            except json.JSONDecodeError:
                print(f"  Error decoding JSON for {game_pk}")
            except Exception as e:
                print(f"  An unexpected error occurred for {game_pk}: {e}")
            
            time.sleep(1) # Pause for 1 second to avoid overwhelming the API

    print(f"\nFastball data collection complete. Data saved to '{output_csv_filename}'")

except Exception as e:
    print(f"An error occurred during script execution: {e}")
