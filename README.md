# Instagram Alter Ego Bot 🤖

An AI-powered Instagram bot that acts as your chaotic alter ego using Azure OpenAI, with persistent memory and ManyChat integration.

## 🔥 Features

- **Persistent Memory**: SQLite database stores all conversations forever
- **Function Calling**: AI dynamically calls games, roasts, hype modes
- **User Isolation**: Each user has completely separate conversation history
- **ManyChat Integration**: Clean API for reliable Instagram connectivity
- **Games**: Emoji puzzles, quick math, number guessing, roast battles
- **Personality**: Gen-z slang, witty responses, chaotic energy

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run the Bot
```bash
# Simple version (direct Instagram, rate limited)
python bot_harsha.py

# Memory API version (recommended for production)
python harsha_complete_api.py
```

## 📡 API Endpoints

- `POST /chat` - Main conversation endpoint
- `GET /memory/{user_id}` - Get conversation history
- `GET /stats` - Global bot statistics

### Example Request:
```json
POST /chat
{
  "message": "hey harsha",
  "user_id": "instagram_12345"
}
```

### Example Response:
```json
{
  "response": "yooo! 🚀 what's poppin?",
  "user_stats": {"total_messages": 1, "games_won": 0},
  "has_memory": true,
  "processing_time_ms": 850.2
}
```

## 🔗 ManyChat Integration

### Setup in ManyChat:
1. Create "External Request" action
2. URL: `https://your-api-url.com/chat`
3. Method: `POST`
4. Body:
```json
{
  "message": "{{last_input_text}}",
  "user_id": "{{contact.id}}",
  "user_name": "{{contact.first_name}}"
}
```

## 🎮 Available Games

- **Emoji Game**: `emoji` - Decode movie emojis
- **Quick Math**: `math` - Fast arithmetic challenges  
- **Number Guess**: `guess` - Guess 1-10 with hints
- **Roast Battle**: `roast` - Get playfully roasted
- **Hype Mode**: `hype` - Get motivated
- **Vibe Check**: `vibe` - Random vibe assessment

## 💾 Database Structure

**Conversations Table:**
- `user_id` - Unique identifier per user
- `message` - User's message
- `response` - Bot's response
- `timestamp` - When conversation happened

**User Stats Table:**
- `user_id` - User identifier
- `total_messages` - Message count
- `games_won` - Games won count
- `last_active` - Last interaction time

## 🧠 Memory System

The bot remembers:
- **All conversations** - Every message ever sent
- **User preferences** - Food likes, conversation topics
- **Game performance** - Win/loss streaks
- **Context awareness** - References previous chats naturally

## 🔒 Privacy & Security

- **User Isolation**: Each user's data is completely separate
- **No Cross-Contamination**: Users never see other conversations
- **Local Database**: All data stored locally in SQLite
- **No Sensitive Data**: Only conversation content stored

## 📁 File Structure

```
ig_alter_ego/
├── harsha_complete_api.py    # 🌟 Main API with memory (RECOMMENDED)
├── bot_harsha.py            # Direct Instagram version
├── bot_azure.py             # Azure-only version
├── requirements.txt         # Dependencies
├── .env.example            # Environment template
├── harsha_memory.db        # SQLite database (auto-created)
└── README.md              # This file
```

## ⚙️ Environment Variables

```env
# Instagram (for direct versions)
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_api_key
AZURE_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/
AZURE_DEPLOYMENT=gpt-5-chat
AZURE_API_VERSION=2024-12-01-preview

# Bot Personality
ALTER_EGO_PERSONALITY="Custom personality prompt here"
```

## 🚀 Deployment

### Railway/Heroku:
1. Push to GitHub
2. Connect to Railway/Heroku
3. Set environment variables
4. Deploy
5. Use API URL in ManyChat

### Local Testing:
```bash
python harsha_complete_api.py
curl -X POST http://localhost:5001/chat -H 'Content-Type: application/json' -d '{"message":"hey", "user_id":"test"}'
```

## 🎯 Why This Approach?

**Direct Instagram APIs** = Rate limits, account bans, constant issues  
**ManyChat + Our API** = Reliable, scalable, professional

## 📊 Monitoring

- Check `bot.log` for detailed activity
- Use `/stats` endpoint for global metrics  
- Use `/memory/{user_id}` to debug user conversations

## 🔧 Troubleshooting

**Memory not persisting?**
- Check if `harsha_memory.db` exists
- Verify write permissions

**API errors?**
- Check Azure OpenAI credentials
- Verify endpoint URL format

**ManyChat not connecting?**
- Ensure API is publicly accessible
- Check webhook URL in ManyChat settings

---

Built with ❤️ for chaotic conversations and persistent memories!