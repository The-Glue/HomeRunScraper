import pandas as pd
import csv

df = pd.read_csv('fastballs_2025.csv')
max_speed_indices = df.groupby('pitcherName')['pitchSpeed'].idxmax()
maxvelo_2025 = df.loc[max_speed_indices]
maxvelo_2025_sorted = maxvelo_2025.sort_values(by='pitchSpeed', ascending=False)
maxvelo_2025_sorted.to_csv('maxvelo_2025.csv', index=False)
