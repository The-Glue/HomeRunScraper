import pandas as pd
import requests
import json
from datetime import datetime
import time

# Assuming you have the TEAM_ABBREV_TO_FULL mapping
TEAM_ABBREV_TO_FULL = {
    'BAL': 'Baltimore Orioles', 'BOS': 'Boston Red Sox', 'NYY': 'New York Yankees',
    'TB': 'Tampa Bay Rays', 'TOR': 'Toronto Blue Jays', 'CWS': 'Chicago White Sox',
    'CLE': 'Cleveland Guardians', 'DET': 'Detroit Tigers', 'KC': 'Kansas City Royals',
    'MIN': 'Minnesota Twins', 'HOU': 'Houston Astros', 'LAA': 'Los Angeles Angels',
    'ATH': 'Athletics',
    'SEA': 'Seattle Mariners', 'TEX': 'Texas Rangers',
    'ATL': 'Atlanta Braves', 'MIA': 'Miami Marlins', 'NYM': 'New York Mets',
    'PHI': 'Philadelphia Phillies', 'WSH': 'Washington Nationals', 'CHC': 'Chicago Cubs',
    'CIN': 'Cincinnati Reds', 'MIL': 'Milwaukee Brewers', 'PIT': 'Pittsburgh Pirates',
    'STL': 'St. Louis Cardinals', 'AZ': 'Arizona Diamondbacks',
    'COL': 'Colorado Rockies',
    'LAD': 'Los Angeles Dodgers', 'SD': 'San Diego Padres', 'SF': 'San Francisco Giants'
}

def get_gamepk_from_schedule(df_schedule, hr_date_str, hr_team_full, vs_team_full):
    """
    Retrieves the gamePk from the schedule DataFrame based on date and teams.
    """
    mask = (
        (df_schedule['date'] == hr_date_str) &
        (
            ((df_schedule['homeTeam'] == hr_team_full) & (df_schedule['awayTeam'] == vs_team_full)) |
            ((df_schedule['homeTeam'] == vs_team_full) & (df_schedule['awayTeam'] == hr_team_full))
        )
    )
    matches = df_schedule[mask]
    if not matches.empty:
        gamepks = matches['gamePk'].tolist()
        return '|'.join(map(str, [int(pk) for pk in gamepks])) if len(gamepks) > 1 else str(int(gamepks[0]))
    return None

def populate_gamepk_if_empty_final(homeruns_csv='2025_homeruns_running.csv', schedule_csv='mlb_schedule_2025.csv'):
    """
    Checks for empty 'gamePk' cells and populates them using the schedule.
    Ensures gamePk is saved as an integer string.
    """
    try:
        df_hr = pd.read_csv(homeruns_csv, parse_dates=['Date'])
        df_schedule = pd.read_csv(schedule_csv)

        populated_count = 0

        for index, row in df_hr.iterrows():
            game_pks_str = row.get('gamePk')
            hr_date = row['Date']
            hr_team_abbr = row['Team']
            vs_team_abbr = row['Vs.']

            if pd.isna(game_pks_str):
                hr_date_str_schedule = hr_date.strftime('%Y-%m-%d')
                hr_team_full = TEAM_ABBREV_TO_FULL.get(hr_team_abbr)
                vs_team_full = TEAM_ABBREV_TO_FULL.get(vs_team_abbr)

                correct_gamepk = get_gamepk_from_schedule(df_schedule, hr_date_str_schedule, hr_team_full, vs_team_full)
                if correct_gamepk:
                    df_hr.at[index, 'gamePk'] = correct_gamepk
                    print(f"Populated empty gamePk for HR on {hr_date_str_schedule} ({hr_team_abbr} vs {vs_team_abbr}) with: {correct_gamepk}")
                    populated_count += 1
                else:
                    print(f"Could not find gamePk in schedule for HR on {hr_date_str_schedule} ({hr_team_abbr} vs {vs_team_abbr}).")

                time.sleep(0.05)

        print(f"\nProcessed {len(df_hr)} home runs.")
        print(f"Populated {populated_count} empty gamePk values.")

        df_hr['gamePk'] = df_hr['gamePk'].astype(str).str.replace('\.0$', '', regex=True) # Remove potential .0
        df_hr.to_csv(homeruns_csv, index=False)
        print(f"Updated {homeruns_csv} with populated gamePk values (ensured integer format).")

    except FileNotFoundError:
        print(f"Error: The file {homeruns_csv} or {schedule_csv} was not found.")
    except KeyError as e:
        print(f"Error: Missing column in DataFrame: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Make sure you have run the code to generate 'mlb_schedule.csv'
    # or have your schedule data in that format.
    populate_gamepk_if_empty_final()
