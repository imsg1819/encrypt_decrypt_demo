'''

import pika
import psycopg2
import base64
import json

DB_HOST = 'localhost'
DB_NAME = 'my_database'
DB_USER = 'postgres'
DB_PASS = 'postgres'

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

        # Encode the plain text
        encrypted_text = base64.b64encode(plain_text.encode()).decode()

        # Store the encoded text and plain text in the database
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO encrypted_texts (id, encrypted_text, plain_text) VALUES (%s, %s, %s)",
                            (unique_id, encrypted_text, plain_text))
        conn.close()

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='encoding_queue')
    channel.basic_consume(queue='encoding_queue', on_message_callback=on_message_received, auto_ack=True)
    print("Waiting for messages...")
    channel.start_consuming()

if __name__ == '__main__':
    main()
'''

