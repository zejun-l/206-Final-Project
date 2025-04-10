import requests
from bs4 import BeautifulSoup
import re
import sqlite3

# ----------- Read URLs from Files-----------
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

# ----------- Create and Set Up Frisbee Database -----------
conn = sqlite3.connect('games.db')  
cur = conn.cursor()

# Create table if it doesn't exist
cur.execute('''
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location TEXT,
        game_date TEXT,
        winner TEXT,
        loser TEXT,
        final_score TEXT
    )
''')
conn.commit()

# Clear existing data (comment out after first run to clear)
# cur.execute('DELETE FROM games')
# conn.commit()

# ----------- Scrape and Insert Data into Database -----------
all_games_data = []

session = requests.Session() 

def clean_team_name(name):
    return re.sub(r'\s*\(\d+\)', '', name).strip()

def is_valid_score(score):
    # Check if score is valid (not a forfiet or 0-0)
    return score != "0-0" and "F-" not in score and "-F" not in score

new_games_count = 0
max_new_games = 25

for event_url, schedule_url in zip(event_urls, schedule_urls):
    if new_games_count >= max_new_games:
        break
    
    # Get city and state from event page
    event_response = session.get(event_url)
    event_soup = BeautifulSoup(event_response.content, 'html.parser')

    info_div = event_soup.find('div', class_='eventInfo2')
    info_text = info_div.get_text(separator=' ', strip=True) if info_div else ''

    pattern = r'City:\s*(.*?)\s+Date:\s*.*?\s+State:\s*([A-Z]{2})'
    match = re.search(pattern, info_text)

    city = match.group(1) if match else None
    state = match.group(2) if match else None
    location = f"{city}, {state}" if city and state else None

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

        # Get the date
        game_date = game.find('span', class_='date').text.strip()

        # Get the final score 
        final_score = f"{winner_score}-{loser_score}"

        # Skip games with forfeits or 0-0 score
        if not is_valid_score(final_score):
            continue

        # Check if this game is already in the database
        cur.execute('''
            SELECT 1 FROM games
            WHERE location=? AND game_date=? AND winner=? AND loser=? AND final_score=?
        ''', (location, game_date, winner_team, loser_team, final_score))

        # If game already in database, skip
        if cur.fetchone():
            continue  

        # Save to database
        cur.execute('''
            INSERT INTO games (location, game_date, winner, loser, final_score)
            VALUES (?, ?, ?, ?, ?)
        ''', (location, game_date, winner_team, loser_team, final_score))

        game_data = {
            'location': location,
            'game_date': game_date,
            'winner': winner_team,
            'loser': loser_team,
            'final_score': final_score
        }
        
        all_games_data.append(game_data)
        new_games_count += 1

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
