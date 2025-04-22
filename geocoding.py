import sqlite3
import requests

# key for geocoding api
API_KEY = "3065ccb6858f319580bc75c3d499d06e"
base_url = "http://api.openweathermap.org/geo/1.0/direct"

# Open database and create cursor
conn = sqlite3.connect('games.db')  
cur = conn.cursor()

# Get needed data for geocoding api
cur.execute('SELECT games.id, locations.city, states.state FROM games JOIN locations ON games.location_id = locations.id JOIN states ON locations.state_id = states.state_id')
data = cur.fetchall()

# create geocoding table in games db if it doesn't already exist
cur.execute('CREATE TABLE IF NOT EXISTS geocoding (game_id INTEGER PRIMARY KEY, lat INTEGER, lon INTEGER)')
conn.commit()

# get the existing data in the geocoding table, if there is any
cur.execute('SELECT game_id FROM geocoding')
existing_data = cur.fetchall()
existing_ids = []
new_data = []

# add the game id of the existing data to list
for geocode in existing_data:
    existing_ids.append(geocode[0])

# only add a game to the list of coordinates to add to the geocoding table this iteration if it hasn't already
for game in data:
    if game[0] not in existing_ids:
        new_data.append(game)

# limit the coordinates inserted to 25
to_insert = new_data[:25]

# make api calls for each game location to get their coordinates
for game in to_insert:
    # account for location names that consist of multiple cities and limit to the first one
    if "and" in game[1]:
        city = game[1].split()[0]
    else:
        city = game[1]
    
    state = game[2]
    country = "US"
    location = ",".join((city, state, country))

    params = {
        "q": location,
        "limit": 1,
        "appid": API_KEY
    }

    # send request
    page = requests.get(base_url, params=params)

    if page.status_code == 200:
        text = page.json()
        lat = text[0]["lat"]
        lon = text[0]["lon"]

        cur.execute("INSERT INTO geocoding (game_id, lat, lon) VALUES (?, ?, ?)", (game[0], lat, lon))
    else:
        print("failed to get coordinates")

conn.commit()
conn.close()