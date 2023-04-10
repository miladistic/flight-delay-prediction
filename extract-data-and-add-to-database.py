# Import necessary libraries
import requests
import json
import sqlite3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Create a connection to the SQLite database and get a cursor
con = sqlite3.connect('flight.db')
cur = con.cursor()

# Drop the Flights table if it already exists, and create a new one
cur.execute('DROP TABLE IF EXISTS Flights')
cur.execute('''
CREATE TABLE Flights (
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    register TEXT NOT NULL,
    flight_num TEXT NOT NULL,
    airplane TEXT,
    scheduled_date TEXT NOT NULL,
    scheduled_time TEXT NOT NULL,
    actual_date TEXT,
    actual_time TEXT,
    day TEXT NOT NULL,
    status1 TEXT NOT NULL,
    status2 TEXT,
    airline_icao TEXT NOT NULL,
    international INTEGER NOT NULL,
    delay INTEGER,
    ftype TEXT NOT NULL,
    miladi_scheduled DATETIME NOT NULL,
    miladi_actual TEXT,
    id INTEGER NOT NULL PRIMARY KEY,
    airline TEXT NOT NULL
    )
''')

# Define some constants
AIRLINE = 'irc'
URL = 'https://www.airport.ir/NetForm/Service/fids?'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
    'Upgrade-Insecure-Requests': '1',
    'DNT': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate'
}

# Define a function to fetch flight data for a given day
def fetch_data(day):
    # Construct the request parameters
    scheduled_date = f'1402-01-{"0" + str(day)}' if day < 10 else f'1402-01-{str(day)}'
    params = {
        'date': scheduled_date,
        'airline': AIRLINE,
        'AUTH_TOKEN': 9890071
    }
    
    # Set up a session with retry functionality
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=5)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    # Make the request and return the JSON response if successful
    response = session.get(URL, params=params, headers=HEADERS, verify=False)
    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))

# Define a function to parse and insert flight data into the database
def collect_data(data):
    rows_inserted = 0
    for item in data['Flights']:
        # Extract data from the JSON object
        origin = item['origin_icao']
        destination = item['destination_icao']
        register = item['register']
        flight_num = item['flight_num']
        airplane = item['airplane_type']
        airline_icao = item['airline_icao']
        airline = item['airline']
        ftype = item['type_']
        delay = 0 if item['delay'] == 'NULL' else item['delay']
        international = 0 if item['international']=="false" else 1
        scheduled_date = item['scheduled_date']
        scheduled_time = item['scheduled_time']
        actual_date = item['actual_date']
        actual_time = item['actual_time']
        miladi_scheduled = item['miladi_scheduled']
        miladi_actual = item['miladi_actual']
        day = item['dow']
        status1 = item['status1']
        status2 = item['status2']
        vals = [origin,destination,register,flight_num,airplane,airline.upper(),airline_icao,ftype,delay,international,scheduled_date,scheduled_time,actual_date,actual_time,miladi_scheduled,miladi_actual,day,status1,status2]
        sql = """INSERT INTO Flights (origin,destination,register,flight_num,airplane,airline,airline_icao,ftype,delay,international,scheduled_date,scheduled_time,actual_date,actual_time,miladi_scheduled,miladi_actual,day,status1,status2)
                values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?); """
        
        try:
            cur.execute(sql, vals)
            rows_inserted +=1
        except Exception as e:
            print('Error:', e)
            continue
            
    con.commit()
    return rows_inserted

# Fetch data for a range of days
total_rows_inserted = 0
for day in range(1, 15):
    data = fetch_data(day)
    flight_day = scheduled_date = f'1402-01-{"0" + str(day)}' if day < 10 else f'1402-01-{str(day)}'
    if data:
        rows_inserted = collect_data(data)
        total_rows_inserted += rows_inserted
        print('Date:', flight_day, '- Rows Inserted:', rows_inserted)

print('Total Rows Inserted:', total_rows_inserted)
cur.close()