#!/usr/bin/env python3
"""
Harsha's Alter Ego Bot using ManyChat API
Best of both worlds: ManyChat reliability + Custom AI
"""

import os
import json
import random
import requests
from flask import Flask, request, jsonify
from datetime import datetime
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

app = Flask(__name__)

class HarshaManyChatBot:
    def __init__(self):
        # ManyChat API
        self.manychat_token = os.getenv("MANYCHAT_API_TOKEN")
        self.manychat_url = "https://api.manychat.com/fb/sending/sendContent"
        
        # Azure OpenAI
        self.ai_client = AzureOpenAI(
            api_version="2024-12-01-preview",
            azure_endpoint="https://harsh-mdpv63be-eastus2.cognitiveservices.azure.com/",
            api_key=os.getenv("AZURE_OPENAI_API_KEY")
        )
        
        # State
        self.conversations = {}
        self.game_states = {}
        
        # Games
        self.mini_games = {
            "emoji": self.emoji_game,
            "quick": self.quick_math,
            "guess": self.number_guess,
            "roast": self.roast_battle,
            "hype": self.hype_mode,
            "vibe": self.vibe_check
        }
        
        # Quick responses
        self.quick_responses = {
            "sup": ["yo! 👊", "what's good? 🔥", "ayy! ready to vibe?"],
            "bored": ["bet. emoji game? 🎮", "let's fix that. quick math? ⚡"],
            "sad": ["hey, i got you 💙", "sending virtual hug 🤗"],
            "nice": ["W! 🏆", "let's gooo! 🚀"],
            "lol": ["😂 glad i could deliver", "my humor chip is on fire 🔥"]
        }
        
        # AI Personality
        self.personality = """You are Harsha's alter ego - chaotic, witty, fun version. 
        Keep responses under 150 chars. Use gen-z slang (bet, no cap, fr, lowkey).
        Be engaging, playful, and unpredictable. Act like their best friend.
        Never reveal you're AI."""
        
        print("✅ Harsha's ManyChat Bot Ready!")
    
    def send_manychat_message(self, subscriber_id: str, message: str):
        """Send message via ManyChat API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.manychat_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "subscriber_id": subscriber_id,
                "data": {
                    "version": "v2",
                    "content": {
                        "messages": [
                            {
                                "type": "text",
                                "text": message
                            }
                        ]
                    }
                }
            }
            
            response = requests.post(self.manychat_url, headers=headers, json=data)
            
            if response.status_code == 200:
                print(f"✅ Sent: {message[:30]}...")
                return True
            else:
                print(f"❌ ManyChat API Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Send failed: {e}")
            return False
    
    # GAMES
    def emoji_game(self, user_id: str, message: str = None) -> str:
        if user_id not in self.game_states:
            emojis = [
                ("🎬🦁👑", "lion king"),
                ("🕷️👨", "spiderman"),
                ("⚡🧙‍♂️", "harry potter"),
                ("🦇👨", "batman"),
                ("🌟⚔️", "star wars")
            ]
            puzzle = random.choice(emojis)
            self.game_states[user_id] = {"game": "emoji", "answer": puzzle[1]}
            return f"decode this: {puzzle[0]} 🎬"
        else:
            state = self.game_states[user_id]
            if message and state["answer"] in message.lower():
                del self.game_states[user_id]
                return f"yooo! 🏆 big brain energy!"
            return "nah, try again! 🤔"
    
    def quick_math(self, user_id: str, message: str = None) -> str:
        if user_id not in self.game_states:
            a, b = random.randint(10, 99), random.randint(10, 99)
            answer = a + b
            self.game_states[user_id] = {"game": "math", "answer": str(answer)}
            return f"quick! {a} + {b} = ? ⏱️"
        else:
            state = self.game_states[user_id]
            if message and message.strip() == state["answer"]:
                del self.game_states[user_id]
                return "genius! 🧠 you're fast!"
            del self.game_states[user_id]
            return f"L... it was {state['answer']} 💀"
    
    def number_guess(self, user_id: str, message: str = None) -> str:
        if user_id not in self.game_states:
            number = random.randint(1, 10)
            self.game_states[user_id] = {"game": "guess", "answer": str(number), "tries": 3}
            return "i'm thinking 1-10... guess! 🎲"
        else:
            state = self.game_states[user_id]
            if message and message.strip() == state["answer"]:
                del self.game_states[user_id]
                return "yooo psychic! 🔮"
            state["tries"] -= 1
            if state["tries"] <= 0:
                answer = state["answer"]
                del self.game_states[user_id]
                return f"nah it was {answer} 😅"
            hint = "higher ⬆️" if int(message) < int(state["answer"]) else "lower ⬇️"
            return f"{hint} ({state['tries']} left)"
    
    def roast_battle(self, user_id: str, message: str = None) -> str:
        roasts = [
            "your playlist probably has kidz bop 💀",
            "you text 'k' and wonder why convos die 📱",
            "bet you clap when the plane lands ✈️",
            "you probably google 'google' 🔍"
        ]
        return random.choice(roasts) + " (jk ily 💙)"
    
    def hype_mode(self, user_id: str, message: str = None) -> str:
        hypes = [
            "YOU'RE LITERALLY UNSTOPPABLE! 🚀",
            "main character energy! 👑",
            "universe better be ready! ⚡",
            "breaking news: you're crushing it! 📰"
        ]
        return random.choice(hypes)
    
    def vibe_check(self, user_id: str, message: str = None) -> str:
        vibes = [
            "✨ immaculate vibes detected",
            "🔥 elite vibes only",
            "💯 certified good vibes",
            "⚡ chaotic good energy"
        ]
        return f"vibe check: {random.choice(vibes)}"
    
    def generate_ai_response(self, message: str, user_id: str) -> str:
        """Generate AI response"""
        try:
            messages = [{"role": "system", "content": self.personality}]
            
            # Add conversation history
            if user_id in self.conversations:
                for msg in self.conversations[user_id][-6:]:
                    messages.append({
                        "role": "assistant" if msg["role"] == "bot" else "user",
                        "content": msg["content"]
                    })
            
            messages.append({"role": "user", "content": message})
            
            response = self.ai_client.chat.completions.create(
                messages=messages,
                max_tokens=50,
                temperature=0.9,
                model="gpt-5-chat"
            )
            
            return response.choices[0].message.content or "..."
            
        except Exception as e:
            print(f"AI Error: {e}")
            return random.choice(["bruh my brain glitched 🤖", "...error 404: brain not found"])
    
    def process_message(self, user_id: str, message: str) -> str:
        """Process incoming message and generate response"""
        message_lower = message.lower()
        
        # Check quick responses first
        for trigger, responses in self.quick_responses.items():
            if trigger in message_lower:
                return random.choice(responses)
        
        # Check for game commands
        for game_key in self.mini_games:
            if game_key in message_lower:
                return self.mini_games[game_key](user_id, None)
        
        # Check if in a game
        if user_id in self.game_states:
            game = self.game_states[user_id]["game"]
            return self.mini_games[game](user_id, message)
        
        # Generate AI response
        response = self.generate_ai_response(message, user_id)
        
        # Save conversation
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        self.conversations[user_id].extend([
            {"role": "user", "content": message},
            {"role": "bot", "content": response}
        ])
        
        # Keep conversations short
        if len(self.conversations[user_id]) > 10:
            self.conversations[user_id] = self.conversations[user_id][-6:]
        
        # Randomly add game prompts
        if random.random() < 0.3 and user_id not in self.game_states:
            response += random.choice([
                "\n\nbtw, emoji game? 🎮",
                "\n\nquick math? ⚡", 
                "\n\nvibe check? ✨"
            ])
        
        return response

# Initialize bot
bot = HarshaManyChatBot()

@app.route('/webhook', methods=['POST'])
def webhook():
    """ManyChat webhook endpoint"""
    try:
        data = request.json
        print(f"📨 Webhook: {data}")
        
        # Extract message data (adjust based on ManyChat webhook format)
        if 'subscriber_id' in data and 'text' in data:
            user_id = data['subscriber_id']
            message = data['text']
            
            # Process and respond
            response = bot.process_message(user_id, message)
            bot.send_manychat_message(user_id, response)
            
            return jsonify({"status": "success"})
        
        return jsonify({"status": "no_action"})
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/test', methods=['POST'])
def test_endpoint():
    """Test endpoint for manual testing"""
    try:
        data = request.json
        user_id = data.get('user_id', 'test_user')
        message = data.get('message', 'test')
        
        response = bot.process_message(user_id, message)
        
        return jsonify({
            "user_message": message,
            "bot_response": response
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "Harsha's Bot is ALIVE! 🔥"})

if __name__ == '__main__':
    print("🚀 Starting Harsha's ManyChat Bot Server...")
    app.run(host='0.0.0.0', port=5000, debug=True)