#!/usr/bin/env python3
"""
Harsha's Alter Ego API with Persistent Memory + Function Calling
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
        # Azure OpenAI
        self.ai_client = AzureOpenAI(
            api_version="2024-12-01-preview",
            azure_endpoint="https://harsh-mdpv63be-eastus2.cognitiveservices.azure.com/",
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
                "name": "start_number_game",
                "description": "Start a number guessing game", 
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
                "name": "vibe_check",
                "description": "Check and comment on the user's current vibe",
                "parameters": {"type": "object", "properties": {}, "required": []}
            },
            {
                "name": "recall_memory",
                "description": "Reference something from a previous conversation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Topic to recall from memory"}
                    },
                    "required": ["topic"]
                }
            }
        ]
        
        # Quick responses for instant reactions
        self.quick_replies = {
            "sup": ["yo! 👊", "what's good? 🔥", "ayy!"],
            "hey": ["yooo! 🚀", "what's poppin?", "hey hey!"],
            "hi": ["hi there! ✨", "hello hello!", "hiii 💫"],
            "lol": ["😂 comedy mode activated", "glad i'm funny"],
            "thanks": ["anytime! 💯", "gotchu fam ✊", "no cap, always here for you"],
            "bye": ["peace out! ✌️", "catch you later! 🌊", "stay legendary! 👑"]
        }
        
        # Game content
        self.games = {
            "emoji_puzzles": [
                ("🎬🦁👑", "lion king"),
                ("🕷️👨", "spiderman"), 
                ("⚡🧙‍♂️", "harry potter"),
                ("🦇👨", "batman"),
                ("🌟⚔️", "star wars"),
                ("🚢❄️💔", "titanic"),
                ("👻🚫", "ghostbusters"),
                ("🏎️💨", "fast and furious")
            ],
            "roasts": [
                "your playlist probably has kidz bop 💀",
                "you text 'k' and wonder why convos die 📱",
                "bet you clap when the plane lands ✈️",
                "you probably google 'google' 🔍",
                "you def use internet explorer 🐌"
            ],
            "hype": [
                "YOU'RE LITERALLY UNSTOPPABLE! 🚀",
                "main character energy is UNMATCHED! 👑", 
                "universe better be ready for you! ⚡",
                "breaking: you're absolutely crushing it! 📰",
                "legend status: ACHIEVED! 🏆"
            ],
            "vibes": [
                "✨ immaculate vibes detected",
                "🔥 elite vibes only", 
                "💯 certified good vibes",
                "⚡ chaotic good energy",
                "🌊 wavy vibes today",
                "👑 main character energy"
            ]
        }
        
        print("🔥 Harsha's Memory API loaded!")
    
    def init_database(self):
        """Initialize SQLite database for persistent memory"""
        self.conn = sqlite3.connect('harsha_memory.db', check_same_thread=False)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                message_type TEXT DEFAULT 'chat'
            )
        ''')
        
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                preferences TEXT,
                last_active DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_messages INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                games_won INTEGER DEFAULT 0
            )
        ''')
        
        self.conn.commit()
        print("📚 Memory database initialized!")
    
    def save_conversation(self, user_id: str, message: str, response: str, msg_type: str = 'chat'):
        """Save conversation to database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO conversations (user_id, message, response, message_type) VALUES (?, ?, ?, ?)",
                (user_id, message, response, msg_type)
            )
            
            # Update user profile
            cursor.execute(
                "INSERT OR REPLACE INTO user_profiles (user_id, last_active, total_messages) VALUES (?, ?, COALESCE((SELECT total_messages FROM user_profiles WHERE user_id = ?) + 1, 1))",
                (user_id, datetime.now().isoformat(), user_id)
            )
            
            self.conn.commit()
        except Exception as e:
            print(f"DB save error: {e}")
    
    def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversation history from database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT message, response, timestamp, message_type FROM conversations WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                (user_id, limit)
            )
            
            rows = cursor.fetchall()
            history = []
            
            for row in reversed(rows):  # Reverse to get chronological order
                history.extend([
                    {"role": "user", "content": row[0], "timestamp": row[2]},
                    {"role": "assistant", "content": row[1], "timestamp": row[2]}
                ])
            
            return history
        except Exception as e:
            print(f"DB read error: {e}")
            return []
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get user statistics"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    "total_messages": row[4] or 0,
                    "games_played": row[5] or 0,
                    "games_won": row[6] or 0,
                    "last_active": row[3]
                }
            return {"total_messages": 0, "games_played": 0, "games_won": 0}
        except Exception as e:
            print(f"Stats error: {e}")
            return {}
    
    def search_memory(self, user_id: str, topic: str) -> str:
        """Search conversation history for specific topics"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT message, response FROM conversations WHERE user_id = ? AND (message LIKE ? OR response LIKE ?) ORDER BY timestamp DESC LIMIT 3",
                (user_id, f"%{topic}%", f"%{topic}%")
            )
            
            rows = cursor.fetchall()
            if rows:
                memories = []
                for row in rows:
                    memories.append(f"You: {row[0]} | Me: {row[1]}")
                return f"I remember we talked about {topic}: " + " | ".join(memories[:2])
            return f"hmm can't recall us talking about {topic} before"
        except Exception as e:
            print(f"Memory search error: {e}")
            return "my memory is being weird rn"
    
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
    
    def start_number_game(self, user_id: str) -> str:
        number = random.randint(1, 10)
        self.game_states[user_id] = {"type": "guess", "answer": str(number), "tries": 3}
        return "i'm thinking of a number 1-10... guess! 🎲"
    
    def roast_user(self, user_id: str) -> str:
        return random.choice(self.games["roasts"]) + " (jk love you 💙)"
    
    def hype_user(self, user_id: str) -> str:
        return random.choice(self.games["hype"])
    
    def vibe_check(self, user_id: str) -> str:
        return f"vibe check: {random.choice(self.games['vibes'])}"
    
    def recall_memory(self, user_id: str, topic: str) -> str:
        return self.search_memory(user_id, topic)
    
    def handle_function_call(self, user_id: str, function_name: str, arguments: Dict) -> str:
        """Execute function calls from AI"""
        try:
            if function_name == "start_emoji_game":
                return self.start_emoji_game(user_id)
            elif function_name == "start_math_game":
                return self.start_math_game(user_id)
            elif function_name == "start_number_game":
                return self.start_number_game(user_id)
            elif function_name == "roast_user":
                return self.roast_user(user_id)
            elif function_name == "hype_user":
                return self.hype_user(user_id)
            elif function_name == "vibe_check":
                return self.vibe_check(user_id)
            elif function_name == "recall_memory":
                topic = arguments.get("topic", "")
                return self.recall_memory(user_id, topic)
            else:
                return "function not found lol"
        except Exception as e:
            print(f"Function call error: {e}")
            return "something went wrong with that function"
    
    def get_quick_response(self, message: str) -> str:
        """Check for quick response triggers"""
        message_lower = message.lower().strip()
        
        if len(message_lower.split()) <= 2:
            for trigger, responses in self.quick_replies.items():
                if trigger == message_lower or message_lower.startswith(trigger + " "):
                    return random.choice(responses)
        return None
    
    def handle_ongoing_games(self, user_id: str, message: str) -> str:
        """Handle ongoing game responses"""
        if user_id not in self.game_states:
            return None
        
        game = self.game_states[user_id]
        
        if game["type"] == "emoji":
            if game["answer"].lower() in message.lower():
                del self.game_states[user_id]
                # Update stats
                cursor = self.conn.cursor()
                cursor.execute("UPDATE user_profiles SET games_won = COALESCE(games_won, 0) + 1 WHERE user_id = ?", (user_id,))
                self.conn.commit()
                return "yooo! 🏆 big brain energy! another one? or wanna chat?"
            return "nope! try again 🤔 (or say 'skip')"
        
        elif game["type"] == "math":
            if message.strip() == game["answer"]:
                del self.game_states[user_id]
                cursor = self.conn.cursor()
                cursor.execute("UPDATE user_profiles SET games_won = COALESCE(games_won, 0) + 1 WHERE user_id = ?", (user_id,))
                self.conn.commit()
                return "genius! 🧠⚡ you're quick! more math?"
            del self.game_states[user_id]
            return f"nah it was {game['answer']} 💀 but good try!"
        
        elif game["type"] == "guess":
            if message.strip() == game["answer"]:
                del self.game_states[user_id]
                cursor = self.conn.cursor()
                cursor.execute("UPDATE user_profiles SET games_won = COALESCE(games_won, 0) + 1 WHERE user_id = ?", (user_id,))
                self.conn.commit()
                return "yooo psychic! 🔮✨ guess another?"
            
            game["tries"] -= 1
            if game["tries"] <= 0:
                answer = game["answer"]
                del self.game_states[user_id]
                return f"it was {answer}! 😅 wanna try again?"
            
            try:
                guess = int(message.strip())
                target = int(game["answer"])
                hint = "higher ⬆️" if guess < target else "lower ⬇️"
                return f"{hint} ({game['tries']} tries left)"
            except:
                return "just gimme a number 1-10! 🎲"
        
        return None
    
    def generate_ai_response(self, message: str, user_id: str) -> str:
        """Generate AI response with function calling and memory"""
        try:
            # Get conversation history
            history = self.get_conversation_history(user_id, limit=10)
            user_stats = self.get_user_stats(user_id)
            
            # Build context
            system_prompt = f"""You are Harsha's chaotic alter ego. Keep responses under 100 chars.
            Use gen-z slang (bet, no cap, fr, lowkey, hits different, say less).
            Be witty, playful, and unpredictable. Never reveal you're AI.
            
            User stats: {user_stats['total_messages']} messages, {user_stats['games_won']} games won.
            
            You can call functions to:
            - Start games (emoji, math, number guessing)  
            - Roast or hype the user
            - Do vibe checks
            - Recall previous conversations
            
            Use functions when appropriate but also have normal conversations."""
            
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history
            messages.extend(history)
            messages.append({"role": "user", "content": message})
            
            # Call OpenAI with function calling
            response = self.ai_client.chat.completions.create(
                model="gpt-5-chat",
                messages=messages,
                functions=self.functions,
                function_call="auto",
                max_tokens=50,
                temperature=0.9,
                frequency_penalty=0.3,
                presence_penalty=0.3
            )
            
            response_message = response.choices[0].message
            
            # Handle function calls
            if response_message.function_call:
                function_name = response_message.function_call.name
                function_args = json.loads(response_message.function_call.arguments or "{}")
                
                # Execute function
                function_result = self.handle_function_call(user_id, function_name, function_args)
                return function_result
            
            # Regular text response
            return response_message.content or "..."
            
        except Exception as e:
            print(f"AI Error: {e}")
            fallbacks = [
                "my brain just blue-screened 🤖", 
                "error 404: wit not found 💀",
                "bruh my circuits are fried"
            ]
            return random.choice(fallbacks)
    
    def process_message(self, user_id: str, message: str) -> str:
        """Main message processing with memory"""
        if not message or not message.strip():
            return "yo send me something! 👀"
        
        message = message.strip()
        
        # 1. Check for ongoing games first
        game_response = self.handle_ongoing_games(user_id, message)
        if game_response:
            return game_response
        
        # 2. Check for quick responses (for very simple messages)
        quick = self.get_quick_response(message)
        if quick:
            return quick
        
        # 3. Generate AI response with memory and function calling
        ai_response = self.generate_ai_response(message, user_id)
        
        # 4. Save conversation
        self.save_conversation(user_id, message, ai_response)
        
        return ai_response

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Add SQLite database for persistent conversation storage", "activeForm": "Adding SQLite database for persistent conversation storage", "status": "completed"}, {"content": "Create conversation memory retrieval system", "activeForm": "Creating conversation memory retrieval system", "status": "completed"}, {"content": "Add function calling for dynamic interactions", "activeForm": "Adding function calling for dynamic interactions", "status": "completed"}, {"content": "Test memory persistence across API restarts", "activeForm": "Testing memory persistence across API restarts", "status": "in_progress"}]