import pandas as pd
import requests
import time
from bs4 import BeautifulSoup
from tqdm import tqdm

# Load CSV
file_path = "2025_homeruns_running.csv"
df = pd.read_csv(file_path)

# Add new column if missing
if "x/30 ballparks" not in df.columns:
    df["x/30 ballparks"] = None

# Baseball Savant URL template
base_url = "https://baseballsavant.mlb.com/sporty-videos?playId={}"

# Headers to mimic a real browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}

# Function to scrape HR: x/30 parks
def get_hr_park_count(play_id):
    url = base_url.format(play_id)
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract the HR x/30 value using the span ID
        hr_span = soup.find("span", id="hr-x-parks-listener")

        if hr_span:
            return int(hr_span.text.split("/")[0].strip())  # Extract 'x' from 'x/30 parks'

        return None  # If not found
    except Exception as e:
        print(f"Error scraping {play_id}: {e}")
        return None

# Iterate and scrape data
for i, row in tqdm(df.iterrows(), total=len(df)):
    play_id = row["playId"]
    
    if pd.isna(df.at[i, "x/30 ballparks"]):
        x_30_value = get_hr_park_count(play_id)
        df.at[i, "x/30 ballparks"] = x_30_value

    if i % 100 == 0:
        print(f"Processed {i} home runs, last play_id: {play_id}, x/30: {x_30_value}")

    time.sleep(2)  # Prevent getting blocked

# Save updated CSV
df.to_csv("2025_homeruns_running.csv", index=False)
print("Scraping complete! Data saved.")
