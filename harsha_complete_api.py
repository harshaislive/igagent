#!/usr/bin/env python3
"""
Harsha's Complete Alter Ego API with Persistent Memory + Function Calling
"""

import os
import json
import random
import time
import sqlite3
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import AzureOpenAI
from typing import List, Dict, Any

load_dotenv()

app = Flask(__name__)

class HarshaMemoryAPI:
    def __init__(self):
        # Check required environment variables
        required_env_vars = ["AZURE_OPENAI_API_KEY", "AZURE_ENDPOINT"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Azure OpenAI
        self.ai_client = AzureOpenAI(
            api_version=os.getenv("AZURE_API_VERSION", "2024-12-01-preview"),
            azure_endpoint=os.getenv("AZURE_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY")
        )
        
        # Initialize database
        self.init_database()
        
        # In-memory cache for active games
        self.game_states = {}
        
        # Function definitions for AI
        self.functions = [
            {
                "name": "start_emoji_game",
                "description": "Start an emoji movie guessing game",
                "parameters": {"type": "object", "properties": {}, "required": []}
            },
            {
                "name": "start_math_game", 
                "description": "Start a quick math challenge",
                "parameters": {"type": "object", "properties": {}, "required": []}
            },
            {
                "name": "roast_user",
                "description": "Give a playful roast to the user",
                "parameters": {"type": "object", "properties": {}, "required": []}
            },
            {
                "name": "hype_user",
                "description": "Hype up and motivate the user",
                "parameters": {"type": "object", "properties": {}, "required": []}
            },
            {
                "name": "recall_memory",
                "description": "Reference something from a previous conversation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Topic to recall"}
                    },
                    "required": ["topic"]
                }
            }
        ]
        
        # Quick responses
        self.quick_replies = {
            "sup": ["yo! 👊", "what's good? 🔥"], 
            "hey": ["yooo! 🚀", "what's poppin?"],
            "hi": ["hi there! ✨", "hello!"],
            "lol": ["😂 comedy activated", "glad i'm funny"],
            "thanks": ["anytime! 💯", "gotchu fam ✊"],
            "bye": ["peace out! ✌️", "stay legendary! 👑"]
        }
        
        # Game content
        self.games = {
            "emoji_puzzles": [
                ("🎬🦁👑", "lion king"), ("🕷️👨", "spiderman"), ("⚡🧙‍♂️", "harry potter"),
                ("🦇👨", "batman"), ("🌟⚔️", "star wars"), ("🚢❄️💔", "titanic")
            ],
            "roasts": [
                "your playlist probably has kidz bop 💀",
                "you text 'k' and wonder why convos die 📱",
                "bet you clap when the plane lands ✈️"
            ],
            "hype": [
                "YOU'RE LITERALLY UNSTOPPABLE! 🚀",
                "main character energy! 👑", 
                "universe better be ready! ⚡"
            ]
        }
        
        print("🔥 Memory API loaded!")
    
    def init_database(self):
        """Initialize SQLite database"""
        self.conn = sqlite3.connect('harsha_memory.db', check_same_thread=False)
        
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id TEXT PRIMARY KEY,
                total_messages INTEGER DEFAULT 0,
                games_won INTEGER DEFAULT 0,
                ai_active BOOLEAN DEFAULT FALSE,
                last_active DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        print("📚 Database ready!")
    
    def save_conversation(self, user_id: str, message: str, response: str):
        """Save to database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO conversations (user_id, message, response) VALUES (?, ?, ?)",
                (user_id, message, response)
            )
            
            # Update stats
            cursor.execute(
                "INSERT OR REPLACE INTO user_stats (user_id, last_active, total_messages) VALUES (?, ?, COALESCE((SELECT total_messages FROM user_stats WHERE user_id = ?) + 1, 1))",
                (user_id, datetime.now().isoformat(), user_id)
            )
            
            self.conn.commit()
        except Exception as e:
            print(f"Save error: {e}")
    
    def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversations"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT message, response FROM conversations WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                (user_id, limit)
            )
            
            rows = cursor.fetchall()
            history = []
            
            for row in reversed(rows):
                history.extend([
                    {"role": "user", "content": row[0]},
                    {"role": "assistant", "content": row[1]}
                ])
            
            return history
        except Exception as e:
            print(f"Read error: {e}")
            return []
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get user stats"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT total_messages, games_won, ai_active FROM user_stats WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            
            if row:
                return {"total_messages": row[0] or 0, "games_won": row[1] or 0, "ai_active": bool(row[2])}
            return {"total_messages": 0, "games_won": 0, "ai_active": False}
        except:
            return {"total_messages": 0, "games_won": 0, "ai_active": False}
    
    def set_ai_active(self, user_id: str, active: bool):
        """Set AI active status for user"""
        try:
            cursor = self.conn.cursor()
            # First check if user exists
            cursor.execute("SELECT user_id FROM user_stats WHERE user_id = ?", (user_id,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing user
                cursor.execute(
                    "UPDATE user_stats SET ai_active = ?, last_active = ? WHERE user_id = ?",
                    (active, datetime.now().isoformat(), user_id)
                )
            else:
                # Insert new user
                cursor.execute(
                    "INSERT INTO user_stats (user_id, ai_active, last_active, total_messages, games_won) VALUES (?, ?, ?, 0, 0)",
                    (user_id, active, datetime.now().isoformat())
                )
            
            self.conn.commit()
            print(f"Set AI active for {user_id}: {active}")
        except Exception as e:
            print(f"Error setting AI active: {e}")
    
    def is_ai_active(self, user_id: str) -> bool:
        """Check if AI is active for user"""
        stats = self.get_user_stats(user_id)
        return stats.get("ai_active", False)
    
    def search_memory(self, user_id: str, topic: str) -> str:
        """Search previous conversations"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT message, response FROM conversations WHERE user_id = ? AND (message LIKE ? OR response LIKE ?) ORDER BY timestamp DESC LIMIT 2",
                (user_id, f"%{topic}%", f"%{topic}%")
            )
            
            rows = cursor.fetchall()
            if rows:
                return f"I remember we talked about {topic}! " + " | ".join([f"You said: {row[0]}" for row in rows[:1]])
            return f"hmm don't think we've talked about {topic} before"
        except:
            return "my memory's being weird rn"
    
    def detect_intent(self, message: str) -> str:
        """Use LLM to detect activation/deactivation intent"""
        try:
            intent_prompt = f"""
            Analyze this message and determine if the user wants to:
            1. ACTIVATE an AI alter ego/chatbot 
            2. DEACTIVATE/STOP an AI alter ego/chatbot
            3. NEITHER (normal conversation)

            Message: "{message}"

            Examples:
            - "talk to alter" → activate
            - "I want to chat with your alter ego" → activate  
            - "activate AI" → activate
            - "turn on bot mode" → activate
            - "bye alter" → deactivate
            - "stop the AI" → deactivate
            - "turn off bot" → deactivate
            - "hello there" → neither
            - "how are you" → neither

            Respond with only: "activate", "deactivate", or "neither"
            """
            
            response = self.ai_client.chat.completions.create(
                model=os.getenv("AZURE_DEPLOYMENT", "gpt-5-chat"),
                messages=[{"role": "user", "content": intent_prompt}],
                max_tokens=5,
                temperature=0.1
            )
            
            intent = response.choices[0].message.content.strip().lower()
            return intent if intent in ["activate", "deactivate"] else "neither"
            
        except Exception as e:
            print(f"Intent detection error: {e}")
            # Fallback to keyword detection
            message_lower = message.lower()
            if any(word in message_lower for word in ["talk to alter", "activate", "turn on", "start ai", "bot mode"]):
                return "activate"
            elif any(word in message_lower for word in ["bye alter", "deactivate", "turn off", "stop", "disable"]):
                return "deactivate"
            return "neither"
    
    # FUNCTION IMPLEMENTATIONS
    def start_emoji_game(self, user_id: str) -> str:
        puzzle = random.choice(self.games["emoji_puzzles"])
        self.game_states[user_id] = {"type": "emoji", "answer": puzzle[1]}
        return f"decode this movie: {puzzle[0]} 🎬"
    
    def start_math_game(self, user_id: str) -> str:
        a, b = random.randint(10, 99), random.randint(10, 99)
        answer = a + b
        self.game_states[user_id] = {"type": "math", "answer": str(answer)}
        return f"quick maths! {a} + {b} = ? ⏱️"
    
    def roast_user(self, user_id: str) -> str:
        return random.choice(self.games["roasts"]) + " (jk love you 💙)"
    
    def hype_user(self, user_id: str) -> str:
        return random.choice(self.games["hype"])
    
    def recall_memory(self, user_id: str, topic: str) -> str:
        return self.search_memory(user_id, topic)
    
    def handle_function_call(self, user_id: str, function_name: str, arguments: Dict) -> str:
        """Execute AI function calls"""
        try:
            if function_name == "start_emoji_game":
                return self.start_emoji_game(user_id)
            elif function_name == "start_math_game":
                return self.start_math_game(user_id)
            elif function_name == "roast_user":
                return self.roast_user(user_id)
            elif function_name == "hype_user":
                return self.hype_user(user_id)
            elif function_name == "recall_memory":
                topic = arguments.get("topic", "")
                return self.recall_memory(user_id, topic)
            else:
                return "function not found lol"
        except Exception as e:
            print(f"Function error: {e}")
            return "something went wrong"
    
    def get_quick_response(self, message: str) -> str:
        """Quick responses for simple messages"""
        message_lower = message.lower().strip()
        
        if len(message_lower.split()) <= 2:
            for trigger, responses in self.quick_replies.items():
                if trigger == message_lower:
                    return random.choice(responses)
        return None
    
    def handle_ongoing_games(self, user_id: str, message: str) -> str:
        """Handle active games"""
        if user_id not in self.game_states:
            return None
        
        game = self.game_states[user_id]
        
        if game["type"] == "emoji":
            if game["answer"].lower() in message.lower():
                del self.game_states[user_id]
                # Update wins
                cursor = self.conn.cursor()
                cursor.execute("UPDATE user_stats SET games_won = COALESCE(games_won, 0) + 1 WHERE user_id = ?", (user_id,))
                self.conn.commit()
                return "yooo! 🏆 big brain energy! another?"
            return "nope! try again 🤔"
        
        elif game["type"] == "math":
            if message.strip() == game["answer"]:
                del self.game_states[user_id]
                cursor = self.conn.cursor()
                cursor.execute("UPDATE user_stats SET games_won = COALESCE(games_won, 0) + 1 WHERE user_id = ?", (user_id,))
                self.conn.commit()
                return "genius! 🧠⚡ more math?"
            del self.game_states[user_id]
            return f"nah it was {game['answer']} 💀"
        
        return None
    
    def generate_ai_response(self, message: str, user_id: str) -> str:
        """AI with memory and functions"""
        try:
            history = self.get_conversation_history(user_id, limit=8)
            stats = self.get_user_stats(user_id)
            
            system_prompt = f"""You are Harsha's chaotic alter ego. Keep responses under 100 chars.
            Use gen-z slang (bet, no cap, fr, lowkey, say less). Be witty and unpredictable.
            
            User has sent {stats['total_messages']} messages, won {stats['games_won']} games.
            Use functions when appropriate. Remember previous conversations."""
            
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(history[-6:])  # Last 6 messages for context
            messages.append({"role": "user", "content": message})
            
            response = self.ai_client.chat.completions.create(
                model=os.getenv("AZURE_DEPLOYMENT", "gpt-5-chat"),
                messages=messages,
                functions=self.functions,
                function_call="auto",
                max_tokens=50,
                temperature=0.9
            )
            
            response_message = response.choices[0].message
            
            # Handle function calls
            if response_message.function_call:
                function_name = response_message.function_call.name
                function_args = json.loads(response_message.function_call.arguments or "{}")
                return self.handle_function_call(user_id, function_name, function_args)
            
            return response_message.content or "..."
            
        except Exception as e:
            print(f"AI Error: {e}")
            return random.choice(["my brain glitched 🤖", "error 404: wit not found"])
    
    def process_message(self, user_id: str, message: str) -> str:
        """Main processing with memory and AI activation control"""
        if not message.strip():
            return ""
        
        message = message.strip()
        message_lower = message.lower()
        
        # Use LLM to detect activation/deactivation intent
        intent = self.detect_intent(message)
        
        if intent == "activate":
            self.set_ai_active(user_id, True)
            return "🤖 Alter ego activated! Ready to chat with chaotic energy! What's good?"
        
        if intent == "deactivate":
            if self.is_ai_active(user_id):
                self.set_ai_active(user_id, False)
                return "✌️ Alter ego deactivated. Peace out! Say something like 'talk to alter' to reactivate."
            else:
                return ""  # Don't respond if AI wasn't active
        
        # Check if AI is active for this user
        if not self.is_ai_active(user_id):
            return ""  # Return empty response if AI is not active
        
        # AI is active - proceed with normal processing
        
        # 1. Handle ongoing games
        game_response = self.handle_ongoing_games(user_id, message)
        if game_response:
            return game_response
        
        # 2. Quick responses for simple messages
        quick = self.get_quick_response(message)
        if quick:
            return quick
        
        # 3. AI response with memory & functions
        ai_response = self.generate_ai_response(message, user_id)
        
        # 4. Save conversation
        self.save_conversation(user_id, message, ai_response)
        
        return ai_response

# Initialize API
harsha = HarshaMemoryAPI()

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "🔥 Harsha's Memory API is LIVE!",
        "features": ["Persistent Memory", "Function Calling", "Games", "Stats"],
        "endpoints": {
            "chat": "POST /chat",
            "memory": "GET /memory/{user_id}",
            "stats": "GET /stats",
            "health": "GET /health"
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        cursor = harsha.conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat with memory"""
    try:
        data = request.json
        
        if not data or 'message' not in data:
            return jsonify({"error": "Missing 'message'"}), 400
        
        user_id = data.get('user_id', 'anonymous')
        message = data.get('message', '')
        
        start_time = time.time()
        response = harsha.process_message(user_id, message)
        processing_time = time.time() - start_time
        
        # Get stats AFTER processing to reflect any changes made during processing
        stats = harsha.get_user_stats(user_id)
        
        # If response is empty (AI not active), return special status
        if not response:
            return jsonify({
                "response": "",
                "ai_active": False,
                "user_id": user_id,
                "processing_time_ms": round(processing_time * 1000, 2),
                "user_stats": stats,
                "message": "AI not active. Send 'hey harsha' to activate.",
                "timestamp": datetime.now().isoformat()
            })
        
        return jsonify({
            "response": response,
            "ai_active": stats.get("ai_active", False),
            "user_id": user_id,
            "processing_time_ms": round(processing_time * 1000, 2),
            "user_stats": stats,
            "has_memory": len(harsha.get_conversation_history(user_id, 1)) > 0,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({
            "error": "Something went wrong",
            "response": "my circuits are having a moment 🤖"
        }), 500

@app.route('/memory/<user_id>', methods=['GET'])
def get_memory(user_id):
    """Get conversation history"""
    try:
        limit = request.args.get('limit', 10, type=int)
        history = harsha.get_conversation_history(user_id, limit)
        stats = harsha.get_user_stats(user_id)
        
        return jsonify({
            "user_id": user_id,
            "conversation_history": history,
            "stats": stats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stats', methods=['GET'])
def global_stats():
    """Global bot stats"""
    try:
        cursor = harsha.conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT user_id), COUNT(*), SUM(games_won) FROM conversations LEFT JOIN user_stats ON conversations.user_id = user_stats.user_id")
        row = cursor.fetchone()
        
        return jsonify({
            "total_users": row[0] or 0,
            "total_messages": row[1] or 0,
            "total_games_won": row[2] or 0
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Get port from environment (for deployment) or default to 5001
    port = int(os.getenv('PORT', 5001))
    
    print("🚀 Starting Harsha's Complete Memory API...")
    print(f"📡 Available at: http://0.0.0.0:{port}")
    print("💾 Memory: SQLite database (persistent)")
    print("🤖 Features: Function calling, memory recall, user stats")
    print(f"💬 Test: curl -X POST http://localhost:{port}/chat -H 'Content-Type: application/json' -d '{{\"message\":\"hey remember me?\", \"user_id\":\"test123\"}}'")
    
    # Use debug=False in production
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)