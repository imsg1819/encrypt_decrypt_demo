'''

from flask import Flask, request, jsonify
import uuid
import psycopg2
import pika
import json

app = Flask(__name__)

# Database connection details
DB_HOST = 'localhost'
DB_NAME = 'my_database'
DB_USER = 'postgres'
DB_PASS = 'postgres'

# Establish a database connection
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn

def create_tables():
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS stored_values (
                    id VARCHAR(32) PRIMARY KEY,
                    value TEXT NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS encrypted_texts (
                    id VARCHAR(32) PRIMARY KEY,
                    encrypted_text TEXT NOT NULL,
                    plain_text TEXT NOT NULL
                );
            """)
    conn.close()

@app.route('/')
def home():
    return "Hello, World!"

@app.route('/encode', methods=['POST'])
def encode_plain_text():
    data = request.json
    plain_text = data.get('plain_text')

    if plain_text is None:
        return jsonify({"error": "Please provide 'plain_text' in the JSON body."}), 400

    # Generate a unique ID
    unique_id = uuid.uuid4().hex

    # Send message to RabbitMQ
    message = {
        'action': 'encode',
        'text': plain_text,
        'id': unique_id
    }

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='encoding_queue')
    channel.basic_publish(exchange='', routing_key='encoding_queue', body=json.dumps(message))
    connection.close()

    return jsonify({"message": "Encoding request sent successfully!", "unique_id": unique_id})

@app.route('/get_encrypted', methods=['POST'])
def get_encrypted():
    data = request.json
    unique_id = data.get('id')

    if unique_id is None:
        return jsonify({"error": "Please provide 'id' in the JSON body."}), 400

    # Retrieve the encrypted text based on the ID
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT encrypted_text FROM encrypted_texts WHERE id = %s", (unique_id,))
            result = cur.fetchone()

    if result:
        encrypted_text = result[0]
        return jsonify({"unique_id": unique_id, "encrypted_text": encrypted_text})
    else:
        return jsonify({"error": "Invalid ID or not found."}), 404

if __name__ == '__main__':
    create_tables()  # Create tables if they don't exist
    app.run(debug=True, port=4321)
'''



# this above is wrong commented code is correct of only for encoding ------




