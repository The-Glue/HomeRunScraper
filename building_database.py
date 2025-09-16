import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import date, timedelta
from functools import wraps

def retry(max_retries=3, delay=2):
    """Retry decorator to handle connection errors."""
    def retry_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                    else:
                        raise
        return wrapper
    return retry_decorator

@retry(max_retries=3, delay=2)
def fetch_webpage(url, headers):
    """Fetch webpage content with retries."""
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()  # Raise HTTPError for bad responses
    return response

def scrape_baseball_savant_table(url, all_data, headers):
    """
    Scrapes home run data directly from Baseball Savant's webpage.
    
    Args:
        url (str): The URL of the Baseball Savant page to scrape.
        all_data (list): List to append scraped data.
    """
    try:
        # Fetch the webpage content
        print(f"Fetching webpage content for {url}...")
        response = fetch_webpage(url, headers)
        print("Page fetched successfully. Parsing content...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Locate the table containing home run data
        table = soup.find("table", {"id": "search_results"})  # Adjust ID or class based on inspection
        if not table:
            print("Table not found on the page.")
            return all_data
        
        print("Table found. Extracting data...")
        
        # Extract rows from the table body
        rows = []
        for tr in table.find("tbody").find_all("tr"):
            cells = [td.text.strip() for td in tr.find_all("td")]
            
            # Skip blank rows
            if all(cell == '' for cell in cells):
                continue
            
            rows.append(cells)
        
        # Append rows to all_data list
        all_data.extend(rows)
        
        return all_data

    except requests.exceptions.RequestException as e:
        print(f"Failed to scrape data due to connection error: {e}")
        return all_data
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return all_data

def main():
    # Date range
    start_date = date(2025, 3, 27)
    end_date = date(2025, 8, 27)
    delta = end_date - start_date

    # Set up headers to mimic a browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    # List to store all data
    all_data = []
    
    for i in range(delta.days + 1):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Construct URL for the current date
        baseball_savant_url = (
            "https://baseballsavant.mlb.com/statcast_search?hfPT=&hfAB=home%5C.%5C.run%7C&hfGT=R%7C&hfPR=&hfZ=&hfStadium=&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=2025%7C&hfSit=&player_type=batter&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=" + date_str + "&game_date_lt=" + date_str + "&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&hfFlag=&metric_1=&group_by=name-event&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_h_launch_speed&sort_order=desc&chk_event_release_speed=on&chk_event_launch_speed=on&chk_event_launch_angle=on&chk_event_hit_distance_sc=on#results"
        )
        
        # Scrape data for the current date
        all_data = scrape_baseball_savant_table(baseball_savant_url, all_data, headers)
        
        # Add a delay to avoid rate-limiting
        time.sleep(1)
    
    # Convert all_data to DataFrame
    if all_data:
        # Extract headers from the first row
        headers = all_data[0]
        
        # Create DataFrame using the extracted headers
        df = pd.DataFrame(all_data[1:], columns=headers)

        # Save DataFrame to CSV
        df.to_csv("2025_homeruns_running.csv", index=False)
        print("All data successfully saved to all_home_runs_data.csv")
    else:
        print("No data was scraped.")

if __name__ == "__main__":
    main()
