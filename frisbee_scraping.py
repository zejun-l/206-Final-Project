import sqlite3
import requests
from bs4 import BeautifulSoup
import re

# Create table to store championship data
def create_frisbee_database():
    conn = sqlite3.connect('frisbee_database.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS championships (
            year TEXT,
            date TEXT,
            winner TEXT,
            runner_up TEXT,
            score TEXT,
            venue TEXT,
            location TEXT,
            league TEXT
        )
    ''')

    conn.commit()
    conn.close()


# Insert data into database 
def insert_data(league, year, date, winner, runner_up, score, venue, location):
    conn = sqlite3.connect('frisbee_database.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO championships (year, date, winner, runner_up, score, venue, location, league)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (year, date, winner, runner_up, score, venue, location, league))

    conn.commit()
    conn.close()


# Scrape data from UFA Wikipedia page
def scrape_ufa_championships():
    url = "https://en.wikipedia.org/wiki/Ultimate_Frisbee_Association"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the championship table
    table = soup.find("caption", string=lambda t: "Ultimate Frisbee Association championships" in t).find_parent("table")
    
    # Loop through table rows and store data
    for row in table.find_all("tr")[1:]:
        cells = row.find_all(["th", "td"])
        if len(cells) < 7:
            continue

        # Get the year 
        year_cell = cells[0]
        year = year_cell.get_text(strip=True)
        year = re.sub(r'\[.*?\]', '', year).strip() 

        # Get other data
        date = cells[1].get_text(strip=True)
        winner = cells[2].get_text(strip=True)
        score = cells[3].get_text(strip=True)
        runner_up = cells[4].get_text(strip=True)
        venue = cells[5].get_text(strip=True)
        location = cells[6].get_text(strip=True)

        # Skip invalid rows
        if "No champion" in winner or winner == "NA":
            continue
        
        # Insert data into the database
        insert_data("UFA", year, date, winner, runner_up, score, venue, location)


# Scrape data from PUL Wikipedia page
def scrape_pul_championships():
    url = "https://en.wikipedia.org/wiki/Premier_Ultimate_League"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the table that contains the championship data 
    table_caption = soup.find("caption", string=lambda text: text and "PUL champions" in text)
    table = table_caption.find_parent("table")
    
    # Loop through each row in the table 
    for row in table.find_all("tr")[1:]:
        cells = row.find_all(["th", "td"])
        if len(cells) < 7:
            continue

        # Get the year
        year = cells[0].get_text(strip=True).split("[")[0]
        
        # Get other data 
        date = cells[1].get_text(strip=True)
        winner = cells[2].get_text(strip=True)
        score = cells[3].get_text(strip=True)
        runner_up = cells[4].get_text(strip=True)
        venue = cells[5].get_text(strip=True)
        location = cells[6].get_text(strip=True)

        # Skip invalid rows 
        if "Canceled" in winner:
            continue

        # Insert data into the database
        insert_data("PUL", year, date, winner, runner_up, score, venue, location)


# Scrape data from WUL Wikipedia page
def scrape_wul_championships():
    url = "https://en.wikipedia.org/wiki/Western_Ultimate_League"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the table that contains the championship data 
    table_caption = soup.find("caption", string=lambda text: text and "WUL champions" in text)
    table = table_caption.find_parent("table")
    
    # Loop through each row in the table (skip header row)
    for row in table.find_all("tr")[1:]:
        cells = row.find_all(["th", "td"])

        # Skip rows with missing or incomplete data
        if len(cells) < 7:
            continue
        
        # Extract the year (clean citation references if present)
        year = cells[0].get_text(strip=True).split("[")[0]
        
        # Extract the date, winner, score, runner-up, venue, and location
        date = cells[1].get_text(strip=True)
        winner = cells[2].get_text(strip=True)
        score = cells[3].get_text(strip=True)
        runner_up = cells[4].get_text(strip=True)
        venue = cells[5].get_text(strip=True)
        location = cells[6].get_text(strip=True)

        # Skip invalid rows (e.g., canceled events)
        if "Canceled" in winner:
            continue

        # Insert data into the database
        insert_data("WUL", year, date, winner, runner_up, score, venue, location)

# Create the database and table
create_frisbee_database()

# Scrape and store data in database
scrape_ufa_championships()
scrape_pul_championships()
scrape_wul_championships()

# Confirm data has been stored in database
print("Data has been stored in the database.")
