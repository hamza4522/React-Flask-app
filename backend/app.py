from flask import Flask, request, jsonify
import requests
import time
import psycopg2
from flask_cors import CORS  # Import CORS from flask_cors

app = Flask(__name__)
CORS(app)  # Initialize CORS on your Flask app

# PostgreSQL database initialization
def init_db():
    conn = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="postgres"
    )
    conn.autocommit = True  # Set autocommit to True for database creation
    cursor = conn.cursor()
    # Check if the database already exists
    cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'hamza'")
    exists = cursor.fetchone()

    if not exists:
        # Create the database if it doesn't exist
        cursor.execute("CREATE DATABASE hamza")
    cursor.close()
    conn.close()

# Function to create the 'api_calls' table if it doesn't exist
def create_table():
    conn = psycopg2.connect(
        host="localhost",
        database="hamza",
        user="postgres",
        password="postgres"
    )
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_calls (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            response_text TEXT
        )
    ''')
    conn.commit()
    conn.close()

# API endpoint to start making API calls
@app.route('/api/start_api_calls', methods=['POST'])
def start_api_calls():
    data = request.json
    api_url = data.get('api_url')
    frequency = int(data.get('frequency'))  # Number of REST calls per hour
    duration = int(data.get('duration'))    # Duration in hours

    init_db()  # Initialize the database (create if it doesn't exist)
    create_table()  # Create the 'api_calls' table if it doesn't exist

    # Calculate interval in seconds between each API call
    interval = 3600 / frequency  # 3600 seconds = 1 hour

    start_time = time.time()
    end_time = start_time + (duration * 3600)  # Convert duration to seconds

    while time.time() < end_time:
        try:
            response = requests.get(api_url)
            response_text = response.text

            # Store the API response in the database
            store_api_call(response_text)
        except Exception as e:
            print(f"Error making API call: {str(e)}")

        time.sleep(interval)

    return jsonify({'message': 'API calls completed.'})

# Store API call result in the database
def store_api_call(response_text):
    conn = psycopg2.connect(
        host="localhost",
        database="hamza",
        user="postgres",
        password="postgres"
    )
    cursor = conn.cursor()
    insert_query = "INSERT INTO api_calls (response_text) VALUES (%s)"
    cursor.execute(insert_query, (response_text,))
    conn.commit()
    conn.close()

# Route to get all recent API call results
@app.route('/api/recent_api_calls', methods=['GET'])
def get_recent_api_calls():
    conn = psycopg2.connect(
        host="localhost",
        database="hamza",
        user="postgres",
        password="postgres"
    )
    cursor = conn.cursor()
    query = "SELECT * FROM api_calls ORDER BY timestamp DESC"
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()

    recent_api_calls = [{'timestamp': row[1], 'response_text': row[2]} for row in results]
    return jsonify(recent_api_calls)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
    app.run(debug=True)
