import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def create_visualization(x, y):
    # Get correlation coefficient (R value)
    correlation = np.corrcoef(x, y)
    r_value = correlation[0, 1]

    # Make scatter plot
    plt.figure(figsize = (10, 6))
    plt.scatter(x, y, color = 'blue', label = 'Game Day')

    # Make line of best fit
    slope, intercept = np.polyfit(x, y, 1)
    line = (slope * x) + intercept
    plt.plot(x, line, color = 'red', label = 'Line of Best Fit')

    # Label points with date
    for i in range(len(x)):
        plt.text(
            x[i] + 0.2, y[i],
            dates[i],
            fontsize=8,
            rotation=30,
            ha='left',
            va='center'
        )

    # Add correlation coefficient to visualization
    plt.text(
        0.05, 0.95,
        f"Pearson r = {r_value:.2f}",
        transform = plt.gca().transAxes,
        fontsize = 11,
        verticalalignment = 'top'
    )

    # Add line of best fit equation to visualization
    plt.text(
        0.05, 0.90,
        f"Line of Best Fit: y = {slope:.2f}x + {intercept:.2f}",
        transform = plt.gca().transAxes,
        fontsize = 11,
        verticalalignment = 'top'
    )

# Read calculation data from CSV
df = pd.read_csv("calculations.csv")
dates = df['game_date'].values
y = df["average_points"].values

# --- Visualization 1: Wind Speed vs. Points ---

x = df["wind_speed"].values

create_visualization(x, y)

plt.title('Average Wind Speed vs. Average Points Scored')
plt.xlabel('Average Wind Speed (mph)')
plt.ylabel('Average Points Scored')
plt.legend()
plt.grid(True)
plt.tight_layout()

plt.savefig('wind_speed.jpg')
plt.show()

# --- Visualization 2: Precipitation vs. Points ---

x = df["precipitation"].values

create_visualization(x, y)

plt.title('Average Precipitation vs. Average Points Scored')
plt.xlabel('Average Precipitation (hours per day)')
plt.ylabel('Average Points Scored')
plt.legend()
plt.grid(True)
plt.tight_layout()

plt.savefig('precipitation.jpg')
plt.show()

# --- Visualization 3: Temperature vs. Points

x = df["temperature"].values

create_visualization(x, y)

plt.title('Average Max Temperature vs. Average Points Scored')
plt.xlabel('Average Max Temperature (F)')
plt.ylabel('Average Points Scored')
plt.legend()
plt.grid(True)
plt.tight_layout()

plt.savefig('temperature.jpg')
plt.show()
