#!/usr/bin/env python3
"""
Harsha's Alter Ego API - Clean & Simple for ManyChat
"""

import os
import json
import random
import time
from flask import Flask, request, jsonify
from datetime import datetime
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

app = Flask(__name__)

class HarshaAPI:
    def __init__(self):
        # Azure OpenAI
        self.ai_client = AzureOpenAI(
            api_version="2024-12-01-preview",
            azure_endpoint="https://harsh-mdpv63be-eastus2.cognitiveservices.azure.com/",
            api_key=os.getenv("AZURE_OPENAI_API_KEY")
        )
        
        # Memory (in production, use Redis/Database)
        self.conversations = {}
        self.game_states = {}
        
        # Quick responses for instant reactions
        self.quick_replies = {
            "sup": ["yo! 👊", "what's good? 🔥", "ayy!"],
            "hey": ["yooo! 🚀", "what's poppin?", "hey hey!"],
            "hi": ["hi there! ✨", "hello hello!", "hiii 💫"],
            "bored": ["bet. want a game? 🎮", "let's fix that! emoji game?"],
            "sad": ["aw man 💙 want me to hype you up?", "sending good vibes ✨"],
            "lol": ["😂 comedy mode activated", "glad i'm funny"],
            "nice": ["W! 🏆", "let's gooo! 🚀", "ayy that's what i'm talking about!"],
            "thanks": ["anytime! 💯", "gotchu fam ✊", "no cap, always here for you"],
            "bye": ["peace out! ✌️", "catch you later! 🌊", "stay legendary! 👑"]
        }
        
        # Games
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
            "would_you_rather": [
                "🔴 read minds OR 🔵 fly",
                "🔴 pause time OR 🔵 rewind time", 
                "🔴 be invisible OR 🔵 super speed",
                "🔴 control fire OR 🔵 control water",
                "🔴 teleport OR 🔵 time travel",
                "🔴 never sleep OR 🔵 never eat"
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
        
        print("🔥 Harsha's API loaded!")
    
    def get_quick_response(self, message: str) -> str:
        """Check for quick response triggers - only for exact/simple matches"""
        message_lower = message.lower().strip()
        
        # Only match if the message is short and mostly just the trigger word
        if len(message_lower.split()) <= 2:
            for trigger, responses in self.quick_replies.items():
                if trigger == message_lower or message_lower.startswith(trigger + " ") or message_lower.endswith(" " + trigger):
                    return random.choice(responses)
        return None
    
    def handle_game(self, user_id: str, message: str) -> str:
        """Handle game requests and ongoing games"""
        message_lower = message.lower()
        
        # New game requests
        if "emoji" in message_lower or "movie" in message_lower:
            puzzle = random.choice(self.games["emoji_puzzles"])
            self.game_states[user_id] = {"type": "emoji", "answer": puzzle[1]}
            return f"decode this movie: {puzzle[0]} 🎬"
        
        elif "math" in message_lower or "quick" in message_lower:
            a, b = random.randint(10, 99), random.randint(10, 99)
            answer = a + b
            self.game_states[user_id] = {"type": "math", "answer": str(answer)}
            return f"quick maths! {a} + {b} = ? ⏱️"
        
        elif "guess" in message_lower or "number" in message_lower:
            number = random.randint(1, 10)
            self.game_states[user_id] = {"type": "guess", "answer": str(number), "tries": 3}
            return "i'm thinking of a number 1-10... guess! 🎲"
        
        elif "would you rather" in message_lower or "choice" in message_lower:
            choice = random.choice(self.games["would_you_rather"])
            return f"would you rather: {choice}?"
        
        elif "roast" in message_lower:
            return random.choice(self.games["roasts"]) + " (jk love you 💙)"
        
        elif "hype" in message_lower:
            return random.choice(self.games["hype"])
        
        elif "vibe" in message_lower:
            return f"vibe check: {random.choice(self.games['vibes'])}"
        
        # Check ongoing games
        if user_id in self.game_states:
            game = self.game_states[user_id]
            
            if game["type"] == "emoji":
                if game["answer"].lower() in message_lower:
                    del self.game_states[user_id]
                    return "yooo! 🏆 big brain energy! another one? say 'emoji'"
                return "nope! try again 🤔 (or say 'skip')"
            
            elif game["type"] == "math":
                if message.strip() == game["answer"]:
                    del self.game_states[user_id]
                    return "genius! 🧠⚡ you're quick! more math?"
                del self.game_states[user_id] 
                return f"nah it was {game['answer']} 💀 but good try!"
            
            elif game["type"] == "guess":
                if message.strip() == game["answer"]:
                    del self.game_states[user_id]
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
        """Generate AI response"""
        try:
            # Build conversation
            messages = [{
                "role": "system", 
                "content": """You are Harsha's chaotic alter ego. Keep responses under 100 chars.
                Use gen-z slang (bet, no cap, fr, lowkey, hits different).
                Be witty, playful, and unpredictable. Never reveal you're AI.
                Occasionally suggest games (emoji, math, roast, vibe check)."""
            }]
            
            # Add recent context (last 4 messages)
            if user_id in self.conversations:
                for msg in self.conversations[user_id][-4:]:
                    messages.append({
                        "role": "assistant" if msg["from"] == "bot" else "user",
                        "content": msg["text"]
                    })
            
            messages.append({"role": "user", "content": message})
            
            # Call Azure OpenAI
            response = self.ai_client.chat.completions.create(
                messages=messages,
                max_tokens=40,  # Keep it short and snappy
                temperature=0.9,
                model="gpt-5-chat",
                frequency_penalty=0.3,
                presence_penalty=0.3
            )
            
            ai_response = response.choices[0].message.content or "..."
            
            # Randomly add game suggestions (20% chance)
            if random.random() < 0.2:
                games = ["emoji game?", "quick math?", "roast battle?", "vibe check?"]
                ai_response += f" {random.choice(games)} 🎮"
            
            return ai_response
            
        except Exception as e:
            print(f"AI Error: {e}")
            fallbacks = [
                "my brain just blue-screened 🤖", 
                "error 404: wit not found 💀",
                "bruh my circuits are fried",
                "...system reboot needed 🔄"
            ]
            return random.choice(fallbacks)
    
    def save_conversation(self, user_id: str, user_msg: str, bot_response: str):
        """Save conversation for context"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        self.conversations[user_id].extend([
            {"from": "user", "text": user_msg, "time": datetime.now().isoformat()},
            {"from": "bot", "text": bot_response, "time": datetime.now().isoformat()}
        ])
        
        # Keep only last 10 messages
        if len(self.conversations[user_id]) > 10:
            self.conversations[user_id] = self.conversations[user_id][-10:]
    
    def process_message(self, user_id: str, message: str) -> str:
        """Main message processing"""
        if not message or not message.strip():
            return "yo send me something! 👀"
        
        message = message.strip()
        
        # 1. Check for quick responses (instant)
        quick = self.get_quick_response(message)
        if quick:
            return quick
        
        # 2. Handle games
        game_response = self.handle_game(user_id, message)
        if game_response:
            return game_response
        
        # 3. Generate AI response
        ai_response = self.generate_ai_response(message, user_id)
        
        # 4. Save conversation
        self.save_conversation(user_id, message, ai_response)
        
        return ai_response

# Initialize API
harsha = HarshaAPI()

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "🔥 Harsha's Alter Ego API is LIVE!",
        "endpoints": {
            "chat": "POST /chat",
            "health": "GET /health"
        }
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint for ManyChat"""
    try:
        data = request.json
        
        # Validate input
        if not data or 'message' not in data:
            return jsonify({"error": "Missing 'message' field"}), 400
        
        user_id = data.get('user_id', 'anonymous')
        message = data.get('message', '')
        
        # Process message
        start_time = time.time()
        response = harsha.process_message(user_id, message)
        processing_time = time.time() - start_time
        
        # Return response
        return jsonify({
            "response": response,
            "user_id": user_id,
            "processing_time_ms": round(processing_time * 1000, 2),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({
            "error": "Something went wrong",
            "response": "my circuits are having a moment... try again? 🤖"
        }), 500

@app.route('/stats', methods=['GET'])
def stats():
    """Get bot stats"""
    return jsonify({
        "total_conversations": len(harsha.conversations),
        "active_games": len(harsha.game_states),
        "uptime": "Just started!" 
    })

if __name__ == '__main__':
    print("🚀 Starting Harsha's Alter Ego API...")
    print("📡 Available at: http://localhost:5000")
    print("💬 Test with: curl -X POST http://localhost:5000/chat -H 'Content-Type: application/json' -d '{\"message\":\"hey\", \"user_id\":\"test\"}'")
    
    app.run(host='0.0.0.0', port=5000, debug=True)