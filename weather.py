import sqlite3
import openmeteo_requests
import requests_cache
from retry_requests import retry

# type into in terminal to install openmeteo-requests




# ------------------ Setup API client with caching + retry ------------------
cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# ------------------ Connect to SQLite database ------------------
conn = sqlite3.connect("games.db")
cur = conn.cursor()

# ------------------ Create weather table if it doesn’t exist ------------------
cur.execute('''
    CREATE TABLE IF NOT EXISTS weather (
        game_id INTEGER PRIMARY KEY,
        wind_speed_mph REAL,
        temperature_f REAL,
        precipitation_hours REAL,
        FOREIGN KEY(game_id) REFERENCES games(id)
    )
''')

# ------------------ Select up to 25 games missing weather data ------------------
cur.execute('''
    SELECT games.id, dates.game_date, geocoding.lat, geocoding.lon
    FROM games
    JOIN dates ON games.date_id = dates.id
    JOIN geocoding ON games.id = geocoding.game_id
    LEFT JOIN weather ON games.id = weather.game_id
    WHERE weather.game_id IS NULL
    LIMIT 25
''')
games = cur.fetchall() 

# ------------------ Fetch weather data and insert into database ------------------
for game_id, game_date, lat, lon in games:
    try:
        # Convert MM/DD/YYYY -> YYYY-MM-DD
        month, day, year = game_date.split("/")
        date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        # API request parameters
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": date_str,
            "end_date": date_str,
            "daily": ["wind_speed_10m_max", "precipitation_hours", "temperature_2m_max"],
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "timezone": "America/New_York"
        }

        # Make API request
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        daily = response.Daily()

        wind = int(daily.Variables(0).ValuesAsNumpy()[0])
        precip = int(daily.Variables(1).ValuesAsNumpy()[0])
        temp = int(daily.Variables(2).ValuesAsNumpy()[0])

        # Insert into weather table
        cur.execute('''
            INSERT OR REPLACE INTO weather (game_id, wind_speed, temperature, precipitation)
            VALUES (?, ?, ?, ?)
        ''', (game_id, wind, temp, precip))

        print(f"Weather for game {game_id} on {date_str}: Wind={wind} mph, Temp={temp} °F, Precip={precip} hrs")

    except Exception as e:
        print(f"Error with game {game_id} on {game_date}: {e}")

# ------------------ Finalize ------------------
conn.commit()
conn.close()
print(" Weather update complete.")
