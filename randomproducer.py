

from flask import Flask, request, jsonify
import uuid
import psycopg2
import pika
import json
import base64

app = Flask(__name__)


DB_HOST = 'localhost'  # Use the container name as the host
DB_NAME = 'my_database'   # Name of the database you created
DB_USER = 'postgres'      # Default PostgreSQL user
DB_PASS = 'mysecretpassword'  # Password from your environment variable


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
                CREATE TABLE IF NOT EXISTS encrypted_texts (
                    id VARCHAR(32) PRIMARY KEY,
                    encrypted_text TEXT NOT NULL,
                    plain_text TEXT NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS decoded_texts (
                    id VARCHAR(32) PRIMARY KEY,
                    decoded_text TEXT NOT NULL
                );
            """)
    conn.close()

def on_message_received(ch, method, properties, body):
    message = json.loads(body)
    if message['action'] == 'decode':
        encrypted_text = message['text']
        unique_id = message['id']

        # Decode the base64 text
        plain_text = base64.b64decode(encrypted_text).decode()

        # Store the decoded text in the database
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO decoded_texts (id, decoded_text) VALUES (%s, %s)",
                            (unique_id, plain_text))
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

    
    unique_id = uuid.uuid4().hex

    # Encode the plain text
    encrypted_text = base64.b64encode(plain_text.encode()).decode()

    
    message = {
        'action': 'encode',
        'text': encrypted_text,
        'id': unique_id
    }

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='encoding_queue')
    channel.basic_publish(exchange='', routing_key='encoding_queue', body=json.dumps(message))
    connection.close()

    
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO encrypted_texts (id, encrypted_text, plain_text) VALUES (%s, %s, %s)",
                        (unique_id, encrypted_text, plain_text))
    conn.close()

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

@app.route('/decode', methods=['POST'])
def decode_text():
    data = request.json
    encrypted_text = data.get('encrypted_text')

    if encrypted_text is None:
        return jsonify({"error": "Please provide 'encrypted_text' in the JSON body."}), 400

    # Generate a unique ID
    unique_id = uuid.uuid4().hex

    # Send message to RabbitMQ
    message = {
        'action': 'decode',
        'text': encrypted_text,
        'id': unique_id
    }

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='decoding_queue')
    channel.basic_publish(exchange='', routing_key='decoding_queue', body=json.dumps(message))
    connection.close()

    return jsonify({"message": "Decoding request sent successfully!", "unique_id": unique_id})

@app.route('/get_decrypted', methods=['POST'])
def get_decrypted():
    data = request.json
    unique_id = data.get('id')

    if unique_id is None:
        return jsonify({"error": "Please provide 'id' in the JSON body."}), 400

    # Retrieve the decoded text based on the ID
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT decoded_text FROM decoded_texts WHERE id = %s", (unique_id,))
            result = cur.fetchone()

    if result:
        decoded_text = result[0]
        return jsonify({"unique_id": unique_id, "decoded_text": decoded_text})
    else:
        return jsonify({"error": "Invalid ID or not found."}), 404

if __name__ == '__main__':
    create_tables()  # Create tables if they don't exist
    app.run(debug=True, port=4321)
