const express = require('express');
const { Server } = require('socket.io');
const { v4: uuidv4 } = require('uuid');
const Twilio = require('twilio');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

// Initialize Express and Socket.IO
const app = express();
const server = require('http').createServer(app);
const io = new Server(server, {
  cors: {
    origin: '*',
  },
});

// Twilio client setup
const twilioClient = Twilio(process.env.TWILIO_ACCOUNT_SID, process.env.TWILIO_AUTH_TOKEN);

// In-memory storage for chats
const chats = [];

// Middleware to parse incoming JSON and URL-encoded data
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Endpoint for Twilio webhook to receive incoming messages
app.post('/webhook', (req, res) => {
  const messageText = req.body.Body;
  const senderId = req.body.From;

  // Create a new chat object with default 'processed' as false
  const chatId = uuidv4();
  const chat = {
    id: chatId,
    chat: messageText,
    processed: false,
    senderId: senderId,
  };
  chats.push(chat);

    console.log('New chat received');
    console.log('Chat ID:', chatId);
    console.log('Sender ID:', senderId);
    console.log('Message:', messageText);
    

  // Emit the message to any WebSocket listeners
  io.emit('new_message', { text: messageText, senderId: senderId, id: chatId });

  res.json({ status: 'message received', chatId: chatId });
});

// GET API endpoint to retrieve unprocessed chats
app.get('/chats', (req, res) => {
  const unprocessedChats = chats.filter(chat => !chat.processed);
  res.json(unprocessedChats);
});

// POST API endpoint to send a response back to Twilio and mark chat as processed
app.post('/respond', async (req, res) => {
  const { chat_id, response } = req.body;

  // Find the chat by chat_id
  const chat = chats.find(c => c.id === chat_id);
  if (!chat) {
    return res.status(404).json({ error: 'Chat not found' });
  }

  try {
    // Send the response back to the sender on WhatsApp
    await sendWhatsAppMessage(chat.senderId, response);
    
    // Mark the chat as processed
    chat.processed = true;

    res.json({ status: 'response sent', chatId: chat_id });
  } catch (error) {
    console.error('Error sending message:', error);
    res.status(500).json({ error: 'Failed to send message' });
  }
});

// Function to send a WhatsApp message through Twilio
async function sendWhatsAppMessage(to, text) {
  return twilioClient.messages.create({
    from: process.env.TWILIO_WHATSAPP_NUMBER,
    body: text,
    to: to,
  });
}

// Start the server
const PORT = process.env.PORT || 5000;
server.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
