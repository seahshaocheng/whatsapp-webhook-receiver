from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import os
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow WebSocket connections

# Endpoint for WhatsApp webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    # Assuming the WhatsApp message data contains 'text' and 'sender_id' fields
    message_text = data.get('text')
    sender_id = data.get('sender_id')

    # Send the message through WebSocket to your response generator
    socketio.emit('new_message', {'text': message_text, 'sender_id': sender_id})

    return jsonify({'status': 'message received'}), 200

# WebSocket event to receive the response from your response generator
@socketio.on('response_from_generator')
def handle_response(data):
    # Send response back to WhatsApp here
    # This is where you would integrate the WhatsApp API to send a message back
    sender_id = data['sender_id']
    response_text = data['text']
    send_whatsapp_message(sender_id, response_text)  # Implement this function for WhatsApp API

def send_whatsapp_message(sender_id, text):
    # WhatsApp API call to send a message
    # Replace with your WhatsApp API endpoint and access token
    url = f'https://graph.facebook.com/v13.0/your_phone_number_id/messages'
    headers = {
        'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
        'Content-Type': 'application/json'
    }
    data = {
        'messaging_product': 'whatsapp',
        'to': sender_id,
        'type': 'text',
        'text': {'body': text}
    }
    response = requests.post(url, headers=headers, json=data)
    return response

if __name__ == '__main__':
    socketio.run(app, port=5000)
