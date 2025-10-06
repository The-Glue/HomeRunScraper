import pandas as pd
import requests
from bs4 import BeautifulSoup
import os

# Load your CSV
df = pd.read_csv("2025_homeruns_running.csv")

# Output folder for videos
output_folder = "2025_homeruns"
os.makedirs(output_folder, exist_ok=True)

# Base URL format
base_url = "https://baseballsavant.mlb.com/sporty-videos?playId={}"

def get_video_url(play_id):
    url = base_url.format(play_id)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Look for the first .mp4 video link
    video_tag = soup.find("video")
    if video_tag and video_tag.find("source"):
        return video_tag.find("source")["src"]
    return None

# Loop through playIds and download videos
for i, row in df.iterrows():
    play_id = row["playId"]
    video_url = get_video_url(play_id)

    if video_url:
        print(f"Downloading video for playId {play_id}...")
        video_data = requests.get(video_url).content
        filename = os.path.join(output_folder, f"{i+1}_{play_id}.mp4")
        with open(filename, "wb") as f:
            f.write(video_data)
    else:
        print(f"⚠️ No video found for playId {play_id}")
