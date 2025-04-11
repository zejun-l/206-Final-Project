import requests
from bs4 import BeautifulSoup
import re
import sqlite3

# ----------- Read URLs from files-----------
event_urls = []
with open('event_pages.txt') as f:
    for line in f:
        stripped = line.strip()
        if stripped:
            event_urls.append(stripped)

schedule_urls = []
with open('schedule_pages.txt') as f:
    for line in f:
        stripped = line.strip()
        if stripped:
            schedule_urls.append(stripped)

# ----------- Create and set up database ----------- 
conn = sqlite3.connect('games.db')  
cur = conn.cursor()

# Create tables for locations, teams, dates, and games
cur.execute('''
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT,
        state TEXT,
        UNIQUE(city, state)  
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_name TEXT UNIQUE  
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS dates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_date TEXT UNIQUE  
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_id INTEGER,
        date_id INTEGER,
        winner_id INTEGER,
        loser_id INTEGER,
        winner_score INTEGER,  
        loser_score INTEGER,   
        FOREIGN KEY (location_id) REFERENCES locations(id),
        FOREIGN KEY (date_id) REFERENCES dates(id),
        FOREIGN KEY (winner_id) REFERENCES teams(id),
        FOREIGN KEY (loser_id) REFERENCES teams(id)
    )
''')
conn.commit()

# ----------- Clear all tables once (comment out code after first run) ----------- 
# cur.execute('DELETE FROM games')
# cur.execute('DELETE FROM locations')
# cur.execute('DELETE FROM teams')
# cur.execute('DELETE FROM dates')
# conn.commit()

# ----------- Reset autoincrement (comment out code after first run) ----------- 
# cur.execute('''DELETE FROM sqlite_sequence WHERE name='locations' ''')
# cur.execute('''DELETE FROM sqlite_sequence WHERE name='teams' ''')
# cur.execute('''DELETE FROM sqlite_sequence WHERE name='dates' ''')
# cur.execute('''DELETE FROM sqlite_sequence WHERE name='games' ''')
# conn.commit()

# ----------- Scrape and insert data into database----------- 
all_games_data = []

# Insert location into database
def insert_location(city, state):
    cur.execute('''
        INSERT OR IGNORE INTO locations (city, state) VALUES (?, ?)
    ''', (city, state))
    conn.commit()
    
    # Get location ID
    cur.execute('''
        SELECT id FROM locations WHERE city=? AND state=? 
    ''', (city, state))
    return cur.fetchone()[0]

# Insert team name into database
def insert_team(team_name):
    cur.execute('''
        INSERT OR IGNORE INTO teams (team_name) VALUES (?)
    ''', (team_name,))
    conn.commit()

    # Get team ID
    cur.execute('''
        SELECT id FROM teams WHERE team_name=? 
    ''', (team_name,))
    return cur.fetchone()[0]

# Insert game date into database
def insert_game_date(game_date):
    cur.execute('''
        INSERT OR IGNORE INTO dates (game_date) VALUES (?)
    ''', (game_date,))
    conn.commit()
    
    # Get date ID
    cur.execute('''
        SELECT id FROM dates WHERE game_date=? 
    ''', (game_date,))
    return cur.fetchone()[0]

session = requests.Session()

def clean_team_name(name):
    return re.sub(r'\s*\(\d+\)', '', name).strip()

 # Check if score is valid (not a forfeit or 0-0)
def is_valid_score(score):
    return score != "0-0" and "F-" not in score and "-F" not in score

def clean_score(score):
    # Check if the score is a valid number
    try:
        scores = score.split('-')
        winner_score = int(scores[0])
        loser_score = int(scores[1])
        return winner_score, loser_score
    except ValueError:
        return None, None 

max_new_games = 25
new_games_count = 0

# Loop through event and schedule URLs
for event_url, schedule_url in zip(event_urls, schedule_urls):
    # Get city and state from event page
    event_response = session.get(event_url)
    event_soup = BeautifulSoup(event_response.content, 'html.parser')

    info_div = event_soup.find('div', class_='eventInfo2')
    info_text = info_div.get_text(separator=' ', strip=True) if info_div else ''

    pattern = r'City:\s*(.*?)\s+Date:\s*.*?\s+State:\s*([A-Z]{2})'
    match = re.search(pattern, info_text)

    city = match.group(1) if match else None
    state = match.group(2) if match else None
    location_id = insert_location(city, state)

    # Get game results from schedule page
    schedule_response = session.get(schedule_url)
    schedule_soup = BeautifulSoup(schedule_response.content, 'html.parser')
    bracket_games = schedule_soup.find_all('div', class_='bracket_game')

    for game in bracket_games:
        if new_games_count >= max_new_games:
            break 

        winner_area = game.find('div', class_='top_area')
        loser_area = game.find('div', class_='btm_area')
        if not (winner_area and loser_area):
            continue

        winner_score = winner_area.find('span', class_='score').text.strip()
        winner_team_raw = winner_area.find('span', class_='team').text.strip()
        loser_score = loser_area.find('span', class_='score').text.strip()
        loser_team_raw = loser_area.find('span', class_='team').text.strip()

        winner_team = clean_team_name(winner_team_raw)
        loser_team = clean_team_name(loser_team_raw)

        # Insert teams into teams table
        winner_id = insert_team(winner_team)
        loser_id = insert_team(loser_team)

        # Get the date
        game_date = game.find('span', class_='date').text.strip()

        # Use regex to match the date (MM/DD/YYYY)
        match = re.match(r'(\d{1,2}/\d{1,2}/\d{4})', game_date)
        if match:
            game_date = match.group(1)  
    
        # Insert date into dates table
        date_id = insert_game_date(game_date)

        # Clean and convert final score to integers
        winner_score_int, loser_score_int = clean_score(f"{winner_score}-{loser_score}")

        # Checks if score is valid (not 0-0, F-W)
        if not is_valid_score(f"{winner_score}-{loser_score}"):
            print(f"Skipping invalid game: {winner_team} vs {loser_team} ({game_date}) with score {winner_score}-{loser_score}")
            continue  # Skip this game if the score is invalid

        # Make sure score is in correct order
        if winner_score_int < loser_score_int: 
            winner_score_int, loser_score_int = loser_score_int, winner_score_int
            winner_id, loser_id = loser_id, winner_id

        # Check if game is already in the database
        cur.execute(''' 
            SELECT 1 FROM games 
            WHERE location_id=? AND date_id=? AND winner_id=? AND loser_id=? AND winner_score=? AND loser_score=? 
        ''', (location_id, date_id, winner_id, loser_id, winner_score_int, loser_score_int))

        # If game already in database, skip
        existing_game = cur.fetchone()
        if existing_game:
            print(f"Skipping duplicate game: {winner_team} vs {loser_team} ({game_date})")
            continue  

        # Save to database
        cur.execute(''' 
            INSERT INTO games (location_id, date_id, winner_id, loser_id, winner_score, loser_score) 
            VALUES (?, ?, ?, ?, ?, ?) 
        ''', (location_id, date_id, winner_id, loser_id, winner_score_int, loser_score_int))

        game_data = { 
            'location': f"{city}, {state}", 
            'game_date': game_date, 
            'winner': winner_team, 
            'loser': loser_team, 
            'final_score': f"{winner_score_int}-{loser_score_int}" 
        }

        all_games_data.append(game_data)
        new_games_count += 1

        conn.commit()

conn.commit()

# Show how many total entries are in the database
cur.execute('SELECT COUNT(*) FROM games')
total_games = cur.fetchone()[0]
print(f"\nTotal games in database: {total_games}")

# Show how many new entries were added this run
print(f"New games added this run: {new_games_count}")
print('-' * 40)

conn.close()

# Show list of games
for game in all_games_data:
    print(f"Game Date: {game['game_date']}")
    print(f"Location: {game['location']}")
    print(f"Winner: {game['winner']}")
    print(f"Loser: {game['loser']}")
    print(f"Final Score: {game['final_score']}")
    print('-' * 40)
