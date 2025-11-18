# ⚾️ 2025 MLB Home Run Database & X/30 Guessing Game

This repository contains a complete database of **every home run hit** during the 2025 MLB regular season, including video files and the crucial **X/30 metric** (the number of MLB ballparks the HR would have cleared).

The data was built using **Baseball Savant** searches, the official **MLB Stats API**, and web scraping with **BeautifulSoup**.

A **Streamlit** application is included for an interactive **X/30 Guessing Game**. The code is written in Python and executed primarily via Jupyter Notebooks.

**Goal:** This project is intended to serve as a working example for leveraging the MLB Stats API and web scraping techniques in future personal data projects.

---

## ⚙️ Data Pipeline: From Savant to Database

The construction of this database was a three-step process designed to resolve the key identifiers needed for scraping.

### Step 1: Initializing the Home Run List

The initial list of home runs was compiled by creating daily **Baseball Savant** searches and scraping the results.

* A loop was executed for every day of the regular season, resulting in the master list (see the `building_database` notebook).
* **Note:** Initial data required several cleanup lines to handle wonky table scrapes (extra rows/gaps) before moving to API calls. This was a necessary step given the decision to start the project by leveraging Savant searches rather than the MLB API's event feed.

### Step 2: Adding Game and Play IDs (The Crux of the Project)

To get the essential `playID` for video access, we first needed the `gamePK` (Game ID) for each event.

* **Finding `gamePK`:** Following the [MLB Stats API documentation](https://github.com/MajorLeagueBaseball/google-cloud-mlb-hackathon/blob/main/README.md), the 2025 season schedule (downloaded as JSON and converted to a CSV, which is included in this repository) was utilized. Home runs were matched against the schedule by date and teams to add the `gamePK` to the database (`adding_gamePks` notebook).
* **Finding `playID`:** With the `gamePK`, we accessed the full game object for each event via the API endpoint: `https://statsapi.mlb.com/api/v1.1/game/{gamePK}/feed/live`. Code was then run to match player names and event metrics to retrieve the unique `playID` for each home run (`adding_playIDs` notebook).

> **Why we need this:** The `playID` is the critical piece of data that allows us to access the specific Baseball Savant video page and scrape the X/30 metric: `https://baseballsavant.mlb.com/sporty-videos?playId={playID}`.

### Step 3: Scraping X/30 and Video Downloads

Using the final `playID` for each home run, two separate code loops utilized the `BeautifulSoup` library:

1.  Scrape the **X/30 metric** from the corresponding Baseball Savant video page (`adding_x30` notebook).
2.  Download the **video file** for local use (`downloading_videos` notebook).

---

## 🎮 The X/30 Guessing Game (Streamlit App)

The final product is a **Streamlit** application that presents the user with 10 randomly selected home run videos and prompts them to guess the X/30 number before revealing the answer.

* **App Status:** The Streamlit code is based heavily on a previous project ("PitchGuesser"), adapted here for video display and the X/30 mechanic.
* **Current Limitation:** A cloud-hosted version is not yet available due to the storage and bandwidth challenge of serving thousands of video files.
* **Demo:** A local demo of the game is available for viewing **[HERE (Link to Demo Video/GIF)]**.

Stay tuned for updates as a scalable video storage solution is developed!
