import requests
from bs4 import BeautifulSoup
import re
import sqlite3

# ----------- Read URLs from files ----------- 
def read_urls():
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

    return event_urls, schedule_urls


# ----------- Create and set up database ----------- 
def setup_database():
    conn = sqlite3.connect('games.db')
    cur = conn.cursor()

    # Create tables for locations
    cur.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT,
            state TEXT,
            UNIQUE(city, state)
        )
    ''')

    # Create table for teams 
    cur.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT UNIQUE
        )
    ''')

    # Create table for dates
    cur.execute('''
        CREATE TABLE IF NOT EXISTS dates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_date TEXT UNIQUE
        )
    ''')

    # Create table for games
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
    return conn, cur


# ----------- Wipe database ----------- 
def wipe_database(cur, conn):
    wipe = input("Do you want to wipe the database? (Yes/No): ").strip().lower()

    if wipe in ('yes'):
        print("Wiping database tables...")
        cur.execute('DELETE FROM games')
        cur.execute('DELETE FROM locations')
        cur.execute('DELETE FROM teams')
        cur.execute('DELETE FROM dates')
        conn.commit()

        # Reset autoincrement
        cur.execute('DELETE FROM sqlite_sequence WHERE name="locations"')
        cur.execute('DELETE FROM sqlite_sequence WHERE name="teams"')
        cur.execute('DELETE FROM sqlite_sequence WHERE name="dates"')
        cur.execute('DELETE FROM sqlite_sequence WHERE name="games"')
        conn.commit()

        print("Database has been wiped. \n")
    else:
        print("Continuing without wiping the database.\n")


# ----------- Inserting into tables ----------- 
def insert_location(cur, conn, city, state):
    cur.execute('''
        INSERT OR IGNORE INTO locations (city, state) VALUES (?, ?)
    ''', (city, state))
    conn.commit()
    cur.execute('SELECT id FROM locations WHERE city=? AND state=?', (city, state))
    return cur.fetchone()[0]

def insert_team(cur, conn, team_name):
    cur.execute('INSERT OR IGNORE INTO teams (team_name) VALUES (?)', (team_name,))
    conn.commit()
    cur.execute('SELECT id FROM teams WHERE team_name=?', (team_name,))
    return cur.fetchone()[0]

def insert_game_date(cur, conn, game_date):
    cur.execute('INSERT OR IGNORE INTO dates (game_date) VALUES (?)', (game_date,))
    conn.commit()
    cur.execute('SELECT id FROM dates WHERE game_date=?', (game_date,))
    return cur.fetchone()[0]


# ----------- Team and score cleaning ----------- 
# Get correct and cleaned team names 
def clean_team_name(name):
    name = re.sub(r'\s*\(\d+\)', '', name).strip()
    if re.match(r'^(w|l)\s+of', name, re.IGNORECASE):
        return None
    return name

# Check if score is valid (not 0-0 or F-W)
def is_valid_score(score):
    return score != "0-0" and "F-" not in score and "-F" not in score

# Clean the score and convert to integers 
def clean_score(score):
    try:
        scores = score.split('-')
        winner_score = int(scores[0])
        loser_score = int(scores[1])
        return winner_score, loser_score
    except:
        return None, None


# ----------- Scrape and insert data ----------- 
def scrape_event_and_schedule(event_url, schedule_url, cur, conn, max_new_games, new_games_count):
    all_games_data = []
    session = requests.Session()

    # Get city and state from event page
    event_response = session.get(event_url)
    event_soup = BeautifulSoup(event_response.content, 'html.parser')
    info_div = event_soup.find('div', class_='eventInfo2')
    
    if info_div:
        info_text = info_div.get_text(separator=' ', strip=True)
    else:
        info_text = ''

    match = re.search(r'City:\s*(.*?)\s+Date:\s*.*?\s+State:\s*([A-Z]{2})', info_text)

    if match:
        city = match.group(1)
        state = match.group(2)
    else:
        city = None
        state = None

    location_id = insert_location(cur, conn, city, state)

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

        if not (winner_team and loser_team):
            continue

        winner_id = insert_team(cur, conn, winner_team)
        loser_id = insert_team(cur, conn, loser_team)

        game_date = game.find('span', class_='date').text.strip()
        match = re.match(r'(\d{1,2}/\d{1,2}/\d{4})', game_date)
        if match:
            game_date = match.group(1)
            
        date_id = insert_game_date(cur, conn, game_date)

        winner_score_int, loser_score_int = clean_score(f"{winner_score}-{loser_score}")

        if not is_valid_score(f"{winner_score}-{loser_score}"):
            print(f"Skipping invalid game: {winner_team} vs {loser_team} ({game_date}) with score {winner_score}-{loser_score}")
            continue

        if winner_score_int < loser_score_int:
            winner_score_int, loser_score_int = loser_score_int, winner_score_int
            winner_id, loser_id = loser_id, winner_id

        cur.execute('''
            SELECT 1 FROM games 
            WHERE location_id=? AND date_id=? AND winner_id=? AND loser_id=? AND winner_score=? AND loser_score=? 
        ''', (location_id, date_id, winner_id, loser_id, winner_score_int, loser_score_int))

        if cur.fetchone():
            print(f"Skipping duplicate game: {winner_team} vs {loser_team} ({game_date})")
            continue

        cur.execute('''
            INSERT INTO games (location_id, date_id, winner_id, loser_id, winner_score, loser_score) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (location_id, date_id, winner_id, loser_id, winner_score_int, loser_score_int))

        all_games_data.append({
            'location': f"{city}, {state}",
            'game_date': game_date,
            'winner': winner_team,
            'loser': loser_team,
            'final_score': f"{winner_score_int}-{loser_score_int}"
        })

        new_games_count += 1
        conn.commit()

    return new_games_count, all_games_data


# ----------- Output ----------- 
def print_summary(cur, new_games_count):
    cur.execute('SELECT COUNT(*) FROM games')
    total_games = cur.fetchone()[0]
    print(f"\nTotal games in database: {total_games}")
    print(f"New games added this run: {new_games_count}")
    
    if new_games_count == 0:
        print("No new games were added to the database.")
    print('-' * 40)

def print_games(all_games_data):
    for game in all_games_data:
        print(f"Game Date: {game['game_date']}")
        print(f"Location: {game['location']}")
        print(f"Winner: {game['winner']}")
        print(f"Loser: {game['loser']}")
        print(f"Final Score: {game['final_score']}")
        print('-' * 40)


# ----------- Main function ----------- 
def main():
    event_urls, schedule_urls = read_urls()
    conn, cur = setup_database()
    wipe_database(cur, conn)

    max_new_games = 25
    new_games_count = 0
    all_games_data = []

    for event_url, schedule_url in zip(event_urls, schedule_urls):
        if new_games_count >= max_new_games:
            break
        new_games_count, games = scrape_event_and_schedule(event_url, schedule_url, cur, conn, max_new_games, new_games_count)
        all_games_data.extend(games)

    conn.commit()
    print_summary(cur, new_games_count)
    conn.close()
    print_games(all_games_data)

if __name__ == '__main__':
    main()
