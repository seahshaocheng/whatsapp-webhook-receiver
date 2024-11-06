from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from twilio.rest import Client
import os
import secrets
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
socketio = SocketIO(app, cors_allowed_origins="*")

# Twilio credentials
account_sid = os.getenv('TWILIO_ACCOUNT_SID', 'your_account_sid')
auth_token = os.getenv('TWILIO_AUTH_TOKEN', 'your_auth_token')
twilio_whatsapp_number = 'whatsapp:+your_twilio_sandbox_number'
client = Client(account_sid, auth_token)

# In-memory storage for chats
chats = []

# Endpoint for Twilio webhook to receive incoming messages
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.form
    message_text = data.get('Body')
    sender_id = data.get('From')
    
    # Create a new chat object with default 'processed' as False
    chat_id = str(uuid.uuid4())
    chat = {
        'id': chat_id,
        'chat': message_text,
        'processed': False
    }
    chats.append(chat)
    
    # Emit the message to any WebSocket listeners
    socketio.emit('new_message', {'text': message_text, 'sender_id': sender_id, 'id': chat_id})
    
    return jsonify({'status': 'message received', 'chat_id': chat_id}), 200

# GET API endpoint to retrieve unprocessed chats
@app.route('/chats', methods=['GET'])
def get_unprocessed_chats():
    unprocessed_chats = [chat for chat in chats if not chat['processed']]
    return jsonify(unprocessed_chats), 200

# POST API endpoint to send a response back to Twilio and mark chat as processed
@app.route('/respond', methods=['POST'])
def respond_to_chat():
    data = request.json
    chat_id = data.get('chat_id')
    response_text = data.get('response')
    
    # Find the chat by chat_id
    chat = next((chat for chat in chats if chat['id'] == chat_id), None)
    
    if not chat:
        return jsonify({'error': 'Chat not found'}), 404
    
    # Send the response back to the sender on WhatsApp
    sender_id = chat.get('sender_id')
    send_whatsapp_message(sender_id, response_text)
    
    # Mark the chat as processed
    chat['processed'] = True
    
    return jsonify({'status': 'response sent', 'chat_id': chat_id}), 200

# Function to send a WhatsApp message through Twilio
def send_whatsapp_message(to, text):
    message = client.messages.create(
        from_=twilio_whatsapp_number,
        body=text,
        to=to
    )
    return message.sid

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000)
