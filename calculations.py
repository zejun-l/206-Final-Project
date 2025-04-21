import sqlite3
import pandas as pd

# Connect to the SQLite database
conn = sqlite3.connect("games.db")  # Adjust path if needed

# Query to join games, dates, and weather using full table names
query = """
SELECT 
    dates.game_date,
    games.id AS game_id,
    games.winner_score,
    games.loser_score,
    weather.wind_speed,
    weather.temperature,
    weather.precipitation
FROM games
JOIN dates ON games.date_id = dates.id
JOIN weather ON games.id = weather.game_id
"""

# Load data into a DataFrame
df = pd.read_sql_query(query, conn)
conn.close()

# Calculate average points scored per game
df["average_points"] = (df["winner_score"] + df["loser_score"]) / 2

# Group by game_date and calculate averages
grouped = df.groupby("game_date").agg({
    "average_points": "mean",
    "wind_speed": "mean",
    "precipitation": "mean",
    "temperature": "mean"
}).reset_index()

grouped.to_csv("calculations.csv", index = False)
