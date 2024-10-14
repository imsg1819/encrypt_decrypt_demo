"""
import pika
import psycopg2
import base64
import json


DB_HOST = 'localhost'  # Use the container name as the host
DB_NAME = 'my_database'   # Name of the database you created
DB_USER = 'postgres'      # Default PostgreSQL user
DB_PASS = 'mysecretpassword'  

# Establish a database connection
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn

def on_message_received(ch, method, properties, body):
    message = json.loads(body)

    if message['action'] == 'encode':
        plain_text = message['text']
        unique_id = message['id']

        # Encode the plain text to base64
        encrypted_text = base64.b64encode(plain_text.encode()).decode()

        # Store the encoded text and plain text in the database
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO encrypted_texts (id, encrypted_text, plain_text) VALUES (%s, %s, %s)",
                            (unique_id, encrypted_text, plain_text))
        conn.close()
        print(f"Encoded and stored: {unique_id}")

    elif message['action'] == 'decode':
        encrypted_text = message['text']
        unique_id = message['id']

        # Decode the base64 text to get the original plain text
        try:
            plain_text = base64.b64decode(encrypted_text).decode()
        except Exception as e:
            print("Invalid base64 text:", e)
            return

        # Store the decoded text in the database
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO decoded_texts (id, decoded_text) VALUES (%s, %s)",
                            (unique_id, plain_text))
        conn.close()
        print(f"Decoded and stored: {unique_id}")

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Start consuming from both queues
    channel.basic_consume(queue='encoding_queue', on_message_callback=on_message_received, auto_ack=True)
    channel.basic_consume(queue='decoding_queue', on_message_callback=on_message_received, auto_ack=True)

    print("Waiting for messages...")
    channel.start_consuming()

if __name__ == '__main__':
    main()
"""




import pika
import psycopg2
import base64
import json
import uuid

DB_HOST = 'localhost'  # Use the container name as the host
DB_NAME = 'my_database'  # Name of the database you created
DB_USER = 'postgres'      # Default PostgreSQL user
DB_PASS = 'mysecretpassword'  

# Establish a database connection
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn

def on_message_received(ch, method, properties, body):
    message = json.loads(body)

    if message['action'] == 'encode':
        plain_text = message['text']
        unique_id = message['id']  # Ensure this is unique

        # Encode the plain text to base64
        encrypted_text = base64.b64encode(plain_text.encode()).decode()

        # Store the encoded text and plain text in the database
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                # Insert into encrypted_texts with ON CONFLICT
                cur.execute("""
                    INSERT INTO encrypted_texts (id, encrypted_text, plain_text)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (unique_id, encrypted_text, plain_text))
        conn.close()
        print(f"Encoded and stored: {unique_id}")

    elif message['action'] == 'decode':
        encrypted_text = message['text']
        unique_id = message['id']

        # Decode the base64 text to get the original plain text
        try:
            plain_text = base64.b64decode(encrypted_text).decode()
        except Exception as e:
            print("Invalid base64 text:", e)
            return

        # Store the decoded text in the database
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                # Insert into decoded_texts with ON CONFLICT
                cur.execute("""
                    INSERT INTO decoded_texts (id, decoded_text)
                    VALUES (%s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (unique_id, plain_text))
        conn.close()
        print(f"Decoded and stored: {unique_id}")

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Start consuming from both queues
    channel.basic_consume(queue='encoding_queue', on_message_callback=on_message_received, auto_ack=True)
    channel.basic_consume(queue='decoding_queue', on_message_callback=on_message_received, auto_ack=True)

    print("Waiting for messages...")
    channel.start_consuming()

if __name__ == '__main__':
    main()
