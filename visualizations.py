import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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

# === PRINT average calculations ===
print("\n--- Averages Per Game Date ---")
for _, row in grouped.iterrows():
    print(f"Date: {row['game_date']}")
    print(f"  Avg Wind Speed: {row['wind_speed']:.2f} mph")
    print(f"  Avg Precipitation: {row['precipitation']:.2f} hrs")
    print(f"  Avg Temperature: {row['temperature']:.2f}°")
    print(f"  Avg Points: {row['average_points']:.2f}")
    print()

# ===== Function to plot scatter with best fit and correlation =====
def plot_scatter_with_fit(x, y, x_label, y_label, title, point_labels, color):
    coeffs = np.polyfit(x, y, 1)
    fit_line = np.poly1d(coeffs)
    r = np.corrcoef(x, y)[0, 1]

        # --- Manual Line of Best Fit and Correlation ---
    x = np.array(x)
    y = np.array(y)

    x_mean = np.mean(x)
    y_mean = np.mean(y)

    x_diff = x - x_mean
    y_diff = y - y_mean

    numerator = np.sum(x_diff * y_diff)
    denominator = np.sum(x_diff ** 2)

    m = numerator / denominator
    b = y_mean - m * x_mean

    # Best fit function
    fit_line = lambda x_val: m * x_val + b

    # Correlation coefficient (r)
    r_num = np.sum(x_diff * y_diff)
    r_den = np.sqrt(np.sum(x_diff ** 2)) * np.sqrt(np.sum(y_diff ** 2))
    r = r_num / r_den



    #--Printing Line of best fit---
    print("\n--- Line of Best Fit Calculations ---")
    print(f"Title: {title}")
    print(f"Slope (m): {coeffs[0]:.4f}")
    print(f"Intercept (b): {coeffs[1]:.4f}")
    print(f"Equation: y = {coeffs[0]:.2f}x + {coeffs[1]:.2f}")
    print(f"Correlation coefficient (r): {r:.4f}")

    plt.figure(figsize=(8, 6))
    plt.scatter(x, y, color=color, label="Game Dates")
    plt.plot(x, fit_line(x), color='black', linestyle='--', label='Best Fit Line')

    # Use iterrows for labeling
    label_data = pd.DataFrame({
        "x": x,
        "y": y,
        "label": point_labels
    })

    # Dynamic vertical offset based on y-range
    y_range = max(y) - min(y)
    x_range = max(x) - min(x)
    y_offset = y_range * (0.03 if color == "red" else 0.02) 
    x_offset = x_range * (0.04 if color == "red" else 0.01)

    for _, row in label_data.iterrows():
        x_off = x_offset
        y_off = y_offset
        if row["label"] in ["3/17/2024", "3/16/2024"]: # manually fixing placement of overlapping dates
            x_off = x_offset + 0.6
            y_off = y_offset - 0.1
        if row["label"] in ["3/31/2024", "2/11/2024", "2/19/2024"]:  # manually fixing placement of overlapping dates
            x_off = x_offset + 0.8
            y_off = y_offset - 0.2

        # Draw a line from the point to the label
        plt.plot(
            [row["x"], row["x"] + x_off],
            [row["y"], row["y"] + y_off],
            color="red",
            linewidth=0.5,
            linestyle="--",
            zorder=1
        )

        # Moving the label points by x and y offset
        plt.text(
            row["x"] + x_off, 
            row["y"] + y_off, 
            row["label"],
            fontsize=9,
            fontweight='bold',
            ha='center',

        )

    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)


    # eq_text = f"y = {m:.2f}x + {b:.2f}\n" \
    #           f"r = {r:.2f}"
    eq_text = f"y = {coeffs[0]:.2f}x + {coeffs[1]:.2f}\n" f"r = {r:.2f}"
    
    plt.text(
        0.05, 0.95,
        eq_text,
        transform=plt.gca().transAxes,
        fontsize=10,
        verticalalignment='top',
        bbox=dict(facecolor='white', edgecolor='black')
    )

    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# === Visualization 1: Wind Speed vs Average Points Scored ===
plot_scatter_with_fit(
    x=grouped["wind_speed"],
    y=grouped["average_points"],
    x_label="Average Wind Speed (mph)",
    y_label="Average Points Scored",
    title="Wind Speed vs Points Scored",
    point_labels=grouped["game_date"],
    color="blue"
)

# === Visualization 2: Precipitation vs Average Points Scored ===
plot_scatter_with_fit(
    x=grouped["precipitation"],
    y=grouped["average_points"],
    x_label="Average Precipitation (hrs)",
    y_label="Average Points Scored",
    title="Precipitation vs Points Scored",
    point_labels=grouped["game_date"],
    color="green"
)

# === Visualization 3: Temperature vs Average Points Scored ===
plot_scatter_with_fit(
    x=grouped["temperature"],
    y=grouped["average_points"],
    x_label="Average Max Temperature",
    y_label="Average Points Scored",
    title="Max Temperature vs Points Scored",
    point_labels=grouped["game_date"],
    color="red"
)
