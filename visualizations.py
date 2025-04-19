import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

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

# === Visualization 1: Wind Speed vs Average Points Scored ===
plt.figure(figsize=(8, 6))
plt.scatter(grouped["wind_speed"], grouped["average_points"], color='blue')
for i, row in grouped.iterrows():
    plt.text(row["wind_speed"], row["average_points"], row["game_date"], fontsize=8)
plt.xlabel("Average Wind Speed")
plt.ylabel("Average Points Scored")
plt.title("Wind Speed vs Average Points Scored")
plt.grid(True)
plt.tight_layout()
plt.show()

# === Visualization 2: Precipitation vs Average Points Scored ===
plt.figure(figsize=(8, 6))
plt.scatter(grouped["precipitation"], grouped["average_points"], color='green')
for i, row in grouped.iterrows():
    plt.text(row["precipitation"], row["average_points"], row["game_date"], fontsize=8)
plt.xlabel("Average Precipitation")
plt.ylabel("Average Points Scored")
plt.title("Precipitation vs Average Points Scored")
plt.grid(True)
plt.tight_layout()
plt.show()

# === Visualization 3: Temperature vs Average Points Scored ===
plt.figure(figsize=(8, 6))
plt.scatter(grouped["temperature"], grouped["average_points"], color='red')
for i, row in grouped.iterrows():
    plt.text(row["temperature"], row["average_points"], row["game_date"], fontsize=8)
plt.xlabel("Average Temperature")
plt.ylabel("Average Points Scored")
plt.title("Temperature vs Average Points Scored")
plt.grid(True)
plt.tight_layout()
plt.show()
