import pandas as pd
import json
import requests
import time
import unicodedata
import re
from fuzzywuzzy import fuzz

def normalize_and_split_name_v5(name):
    """Handles 'Jr.', multi-word names, and normalizes, attempts to fix last name first with comma."""
    name = name.strip().lower()
    is_jr = False
    if name.endswith(' jr'):
        name = name[:-3].strip()
        is_jr = True
    elif name.endswith(', jr'):
        name = name[:-4].strip()
        is_jr = True

    # Check if the name has a comma followed by a space, suggesting Last, First format
    if ', ' in name:
        parts = name.split(', ')
        if len(parts) == 2:
            last_name_part = parts[0].strip()
            first_name_part = parts[1].strip()
            normalized_first = "".join(c for c in unicodedata.normalize('NFD', first_name_part.lower()) if unicodedata.category(c) != 'Mn' and c.isalnum() or c.isspace())
            normalized_last = "".join(c for c in unicodedata.normalize('NFD', last_name_part.lower()) if unicodedata.category(c) != 'Mn' and c.isalnum() or c.isspace())
            return normalized_first, normalized_last, is_jr

    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    name = re.sub(r'[^a-z\s]', '', name)
    parts = name.strip().split()
    first_name = parts[0] if parts else ""
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
    return first_name, last_name, is_jr

def add_playid_to_homeruns_v5(homeruns_csv='2025_homeruns_running.csv', fuzzy_threshold=80):
    """Version using normalize_and_split_name_v5."""
    try:
        df_hr = pd.read_csv(homeruns_csv, encoding='utf-8')
        if 'playId' not in df_hr.columns:
            df_hr['playId'] = None
        processed_game_pks = set()

        for index, hr_row in df_hr.iterrows():
            possible_game_pks_str = hr_row.get('gamePk')
            if pd.isna(possible_game_pks_str):
                continue
            possible_game_pks = str(possible_game_pks_str).split('|')

            for game_pk in possible_game_pks:
                if game_pk in processed_game_pks:
                    continue

                game_feed_url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
                print(f"Trying URL: {game_feed_url}")
                try:
                    response = requests.get(game_feed_url, timeout=10)
                    response.raise_for_status()
                    game_feed_data = response.json()
                    processed_game_pks.add(game_pk)

                    relevant_hr_indices = df_hr[df_hr['gamePk'].astype(str).str.contains(game_pk, na=False)].index.tolist()
                    relevant_hr_data = df_hr.loc[relevant_hr_indices].to_dict('index')
                    all_plays = game_feed_data.get('liveData', {}).get('plays', {}).get('allPlays', [])

                    for play in all_plays:
                        if play.get('result', {}).get('eventType') == 'home_run':
                            batter_name_feed_raw = play.get('matchup', {}).get('batter', {}).get('fullName')
                            feed_first_norm, feed_last_norm, is_jr_feed = normalize_and_split_name_v5(batter_name_feed_raw)

                            for event in play.get('playEvents', []):
                                potential_play_id = event.get('playId')

                                for hr_index in relevant_hr_indices:
                                    hr_row_match = relevant_hr_data[hr_index]
                                    batter_name_csv_raw = hr_row_match['Name']
                                    csv_first_norm, csv_last_norm, is_jr_csv = normalize_and_split_name_v5(batter_name_csv_raw)

                                    name_match = False
                                    if (csv_first_norm == feed_first_norm and csv_last_norm == feed_last_norm and is_jr_csv == is_jr_feed) or \
                                       (csv_first_norm == feed_last_norm and csv_last_norm == feed_first_norm and is_jr_csv == is_jr_feed):
                                        name_match = True
                                        print(f"\nPotential Name Match (Strict)! CSV Norm: ({csv_first_norm}, {csv_last_norm}, Jr: {is_jr_csv}), Feed Norm: ({feed_first_norm}, {feed_last_norm}, Jr: {is_jr_feed}), CSV Raw: {batter_name_csv_raw}, Feed Raw: {batter_name_feed_raw}, AtBatIndex: {play.get('about', {}).get('atBatIndex')}, PlayEvent ID: {potential_play_id}")
                                    elif fuzz.ratio(f"{csv_first_norm} {csv_last_norm}", f"{feed_first_norm} {feed_last_norm}") >= fuzzy_threshold or \
                                         fuzz.ratio(f"{csv_last_norm} {csv_first_norm}", f"{feed_first_norm} {feed_last_norm}") >= fuzzy_threshold:
                                        if is_jr_csv == is_jr_feed:
                                            name_match = True
                                            print(f"\nPotential Name Match (Fuzzy)! CSV Norm: ({csv_first_norm}, {csv_last_norm}, Jr: {is_jr_csv}), Feed Norm: ({feed_first_norm}, {feed_last_norm}, Jr: {is_jr_feed}), CSV Raw: {batter_name_csv_raw}, Feed Raw: {batter_name_feed_raw}, AtBatIndex: {play.get('about', {}).get('atBatIndex')}, PlayEvent ID: {potential_play_id}, Score: {fuzz.ratio(f'{csv_first_norm} {csv_last_norm}', f'{feed_first_norm} {feed_last_norm}')}")
                                        else:
                                            print(f"No Name Match (Fuzzy - Jr Mismatch) - CSV Norm: ({csv_first_norm}, {csv_last_norm}, Jr: {is_jr_csv}), Feed Norm: ({feed_first_norm}, {feed_last_norm}, Jr: {is_jr_feed}), CSV Raw: {batter_name_csv_raw}, Feed Raw: {batter_name_feed_raw}")
                                    else:
                                        print(f"No Name Match - CSV Norm: ({csv_first_norm}, {csv_last_norm}, Jr: {is_jr_csv}), Feed Norm: ({feed_first_norm}, {feed_last_norm}, Jr: {is_jr_feed}), CSV Raw: {batter_name_csv_raw}, Feed Raw: {batter_name_feed_raw}")

                                    if name_match:
                                        pitch_speed_feed = None
                                        exit_velocity_feed = None
                                        distance_feed = None
                                        la_feed = None
                                        found_hit_data_event = False

                                        if event.get('pitchData'):
                                            pitch_speed_feed = event['pitchData'].get('startSpeed')
                                        hit_data = event.get('hitData', {})
                                        if hit_data:
                                            exit_velocity_feed = hit_data.get('launchSpeed')
                                            distance_feed = hit_data.get('totalDistance')
                                            la_feed = hit_data.get('launchAngle')
                                            found_hit_data_event = True
                                            print("  Found hitData in playEvent.")

                                        try:
                                            pitch_speed_csv = float(hr_row_match.get('Pitch (MPH)', 0))
                                            ev_csv = float(hr_row_match.get('EV (MPH)', 0))
                                            distance_csv = int(hr_row_match.get('Dist (ft)', 0))
                                            la_csv = int(hr_row_match.get('LA (deg)',0))

                                            print(f"  CSV: Pitch={pitch_speed_csv}, EV={ev_csv}, Dist={distance_csv}, LA={la_csv}")
                                            print(f"  Feed: Pitch={pitch_speed_feed}, EV={exit_velocity_feed}, Dist={distance_feed}, LA={la_feed}")

                                            speed_match = abs(pitch_speed_csv - float(pitch_speed_feed)) < 2 if pitch_speed_feed is not None else True
                                            ev_match = abs(ev_csv - float(exit_velocity_feed)) < 2 if exit_velocity_feed is not None else True
                                            distance_match = abs(distance_csv - float(distance_feed)) < 10 if distance_feed is not None else True

                                            if speed_match and ev_match and distance_match and potential_play_id and found_hit_data_event:
                                                df_hr.at[hr_index, 'playId'] = potential_play_id
                                                print(f"  >>> MATCH FOUND! Added playId '{potential_play_id}' for {batter_name_csv_raw} in game {game_pk}")
                                                break
                                            else:
                                                print(f"{speed_match=}, {ev_match=}, {distance_match=}, play_event_id={potential_play_id}, {found_hit_data_event=}")
                                                print("  No metric match found for playEvent with pitchData.")

                                        except ValueError:
                                            print(f"  Warning: Could not convert HR metrics to numbers in CSV for {batter_name_csv_raw} in game {game_pk}")
                                        except KeyError as e:
                                            print(f"  Warning: Missing key in playEvent: {e}")
                    if any(pd.notna(df_hr.loc[relevant_hr_indices, 'playId'])):
                        break

                except requests.exceptions.RequestException as e:
                    print(f"Error fetching game feed for {game_pk}: {e}")
                except json.JSONDecodeError:
                    print(f"Error decoding JSON for game feed {game_pk}")
                except Exception as e:
                    print(f"An unexpected error occurred while processing game feed for {game_pk}: {e}")

                time.sleep(0.1)

        df_hr.to_csv(homeruns_csv, index=False)
        print(f"Finished attempting to add playIds to {homeruns_csv}")

    except FileNotFoundError:
        print(f"Error: The file {homeruns_csv} was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    add_playid_to_homeruns_v5()
