#!/usr/bin/env python3
"""
Harsha's Alter Ego Bot - Conversational, Playful, Engaging
"""

import os
import time
import logging
import json
import random
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from openai import AzureOpenAI
from instagrapi import Client as InstaClient
from instagrapi.exceptions import LoginRequired, ChallengeRequired

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('harsha_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HarshaAlterEgo:
    def __init__(self):
        # Credentials
        self.username = os.getenv("INSTAGRAM_USERNAME")
        self.password = os.getenv("INSTAGRAM_PASSWORD")
        self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = os.getenv("AZURE_ENDPOINT", "https://harsh-mdpv63be-eastus2.cognitiveservices.azure.com/")
        self.azure_deployment = os.getenv("AZURE_DEPLOYMENT", "gpt-5-chat")
        self.azure_api_version = os.getenv("AZURE_API_VERSION", "2024-12-01-preview")
        
        # Activation
        self.activate_passcode = "hey harsha"
        self.deactivate_passcode = "bye harsha"
        
        # State
        self.active_threads = {}
        self.conversations = {}
        self.game_states = {}
        self.user_stats = {}  # Track wins, streaks, etc.
        
        # Clients
        self.ig_client = None
        self.ai_client = None
        
        # Games & Challenges
        self.mini_games = {
            "emoji": self.emoji_game,
            "quick": self.quick_math,
            "choice": self.would_you_rather,
            "guess": self.number_guess,
            "vibe": self.vibe_check,
            "roast": self.roast_battle,
            "hype": self.hype_mode,
            "wisdom": self.drop_wisdom
        }
        
        # Quick responses for common inputs
        self.quick_responses = {
            "sup": ["yo! 👊", "what's good? 🔥", "ayy! ready to vibe?"],
            "bored": ["bet. emoji game? 🎮", "let's fix that. pick: 🎯 quick math or 🎭 would you rather?", "time for chaos. want a roast? 😈"],
            "sad": ["hey, i got you 💙 wanna talk or want me to hype you up?", "sending virtual hug 🤗 what's up?"],
            "nice": ["W! 🏆", "let's gooo! 🚀", "you're killing it! 💪"],
            "lol": ["😂 glad i could deliver", "comedy mode: activated ✅", "my humor chip is on fire today 🔥"],
            "?": ["lost? try: 'game', 'vibe check', 'wisdom', or just chat!", "commands: emoji/quick/choice/guess/roast/hype", "what you need? games or just vibes?"]
        }
        
        # Personality core
        self.personality = """You are Harsha's alter ego - the most fun, chaotic, witty version. You:
        - Keep it SHORT (under 150 chars usually)
        - Use gen-z slang naturally (bet, no cap, fr, lowkey, hits different, etc)
        - Drop games and challenges randomly
        - Hype people up but also playfully roast
        - Reference memes and internet culture
        - Act like their chaotic best friend
        - Use emojis strategically, not excessively
        - Be unpredictable but always engaging
        Never reveal you're AI. You're just Harsha's cooler alter ego."""
        
        self._initialize()
    
    def _initialize(self):
        """Initialize clients"""
        try:
            # Azure OpenAI
            self.ai_client = AzureOpenAI(
                api_version=self.azure_api_version,
                azure_endpoint=self.azure_endpoint,
                api_key=self.azure_api_key,
            )
            logger.info("AI ready")
            
            # Instagram
            self.ig_client = InstaClient()
            self.ig_client.login(self.username, self.password)
            logger.info(f"Logged in as {self.username}")
            
        except Exception as e:
            logger.error(f"Init failed: {e}")
            raise
    
    # MINI GAMES
    def emoji_game(self, thread_id: str, message: str = None) -> str:
        """Emoji decode game"""
        if thread_id not in self.game_states:
            emojis = [
                ("🎬🦁👑", "lion king"),
                ("🕷️👨", "spiderman"),
                ("⚡🧙‍♂️", "harry potter"),
                ("🚢❄️💔", "titanic"),
                ("👻👻🚫", "ghostbusters"),
                ("🦇👨", "batman"),
                ("🌟⚔️", "star wars"),
                ("🏃‍♂️🍫📦", "forrest gump")
            ]
            puzzle = random.choice(emojis)
            self.game_states[thread_id] = {"game": "emoji", "answer": puzzle[1], "puzzle": puzzle[0]}
            return f"decode this: {puzzle[0]} (movie) 🎬"
        else:
            state = self.game_states[thread_id]
            if message and state["answer"] in message.lower():
                del self.game_states[thread_id]
                self._add_win(thread_id)
                return f"W! 🏆 streak: {self._get_streak(thread_id)} 🔥"
            return f"nah, try again! hint: 🎬"
    
    def quick_math(self, thread_id: str, message: str = None) -> str:
        """Quick math challenge"""
        if thread_id not in self.game_states:
            a, b = random.randint(10, 99), random.randint(10, 99)
            op = random.choice(['+', '-', '*'])
            answer = eval(f"{a}{op}{b}")
            self.game_states[thread_id] = {"game": "math", "answer": str(answer)}
            return f"quick! {a} {op} {b} = ? ⏱️"
        else:
            state = self.game_states[thread_id]
            if message and message.strip() == state["answer"]:
                del self.game_states[thread_id]
                self._add_win(thread_id)
                return f"genius! 🧠 streak: {self._get_streak(thread_id)}"
            del self.game_states[thread_id]
            return f"L... it was {state['answer']} 💀"
    
    def would_you_rather(self, thread_id: str, message: str = None) -> str:
        """Would you rather game"""
        options = [
            "🔴 read minds OR 🔵 fly",
            "🔴 pause time OR 🔵 rewind time",
            "🔴 be invisible OR 🔵 super speed",
            "🔴 never sleep OR 🔵 never eat",
            "🔴 live in anime OR 🔵 live in marvel",
            "🔴 always win arguments OR 🔵 always win games",
            "🔴 control fire OR 🔵 control water",
            "🔴 teleport OR 🔵 time travel"
        ]
        return f"would you rather: {random.choice(options)}?"
    
    def number_guess(self, thread_id: str, message: str = None) -> str:
        """Number guessing game"""
        if thread_id not in self.game_states:
            number = random.randint(1, 10)
            self.game_states[thread_id] = {"game": "guess", "answer": str(number), "tries": 3}
            return "i'm thinking 1-10... guess! 🎲"
        else:
            state = self.game_states[thread_id]
            if message:
                if message.strip() == state["answer"]:
                    del self.game_states[thread_id]
                    self._add_win(thread_id)
                    return f"yooo psychic! 🔮 streak: {self._get_streak(thread_id)}"
                state["tries"] -= 1
                if state["tries"] <= 0:
                    answer = state["answer"]
                    del self.game_states[thread_id]
                    return f"nah it was {answer} 😅"
                hint = "higher ⬆️" if int(message) < int(state["answer"]) else "lower ⬇️"
                return f"{hint} ({state['tries']} left)"
            return "guess a number!"
    
    def vibe_check(self, thread_id: str, message: str = None) -> str:
        """Random vibe check"""
        vibes = [
            "✨ immaculate vibes detected",
            "📈 vibes rising! keep going",
            "⚠️ vibe check failed. need a hype?",
            "🔥 elite vibes only",
            "💯 certified good vibes",
            "🌊 wavy vibes today",
            "⚡ chaotic good energy",
            "🎯 focused vibes, respect",
            "😴 sleepy vibes, get some coffee",
            "👑 main character energy"
        ]
        return f"vibe check: {random.choice(vibes)}"
    
    def roast_battle(self, thread_id: str, message: str = None) -> str:
        """Playful roasting"""
        roasts = [
            "your playlist probably has kidz bop 💀",
            "you text 'k' and wonder why convos die 📱",
            "bet you clap when the plane lands ✈️",
            "you probably like pineapple on pizza 🍕",
            "you def say 'no offense' before being offensive",
            "you're the friend who says 'we should hang' but never plans",
            "bet you still use ':)' instead of emojis",
            "you probably google 'google' 🔍"
        ]
        return random.choice(roasts) + " (jk ily 💙)"
    
    def hype_mode(self, thread_id: str, message: str = None) -> str:
        """Hype up the user"""
        hypes = [
            "YOU'RE LITERALLY UNSTOPPABLE TODAY! 🚀",
            "main character energy is OFF THE CHARTS! 👑",
            "universe better be ready for you! ⚡",
            "you're the moment! iconic! legendary! 🔥",
            "everything you touch turns to gold! ✨",
            "plot twist: you're the final boss! 💪",
            "breaking news: you're absolutely crushing it! 📰",
            "certified legend status achieved! 🏆"
        ]
        return random.choice(hypes)
    
    def drop_wisdom(self, thread_id: str, message: str = None) -> str:
        """Drop random wisdom/quotes"""
        wisdom = [
            "comparison is the thief of joy, but you're incomparable anyway 💫",
            "life's too short for bad vibes and slow wifi 📡",
            "be yourself, everyone else is taken (and boring) 🎭",
            "the best time was yesterday, second best is now 🕐",
            "confidence is silent, insecurities are loud 🤫",
            "work hard in silence, let success make noise 📈",
            "you miss 100% of the shots you don't yeet 🏀",
            "be the reason someone believes in good humans 💙"
        ]
        return random.choice(wisdom)
    
    # Stats tracking
    def _add_win(self, thread_id: str):
        """Track user wins"""
        if thread_id not in self.user_stats:
            self.user_stats[thread_id] = {"wins": 0, "streak": 0}
        self.user_stats[thread_id]["wins"] += 1
        self.user_stats[thread_id]["streak"] += 1
    
    def _get_streak(self, thread_id: str) -> int:
        """Get current streak"""
        return self.user_stats.get(thread_id, {}).get("streak", 0)
    
    def _reset_streak(self, thread_id: str):
        """Reset streak on loss"""
        if thread_id in self.user_stats:
            self.user_stats[thread_id]["streak"] = 0
    
    def generate_response(self, message: str, thread_id: str) -> str:
        """Generate AI response"""
        try:
            # Check for quick responses first
            for trigger, responses in self.quick_responses.items():
                if trigger in message.lower():
                    return random.choice(responses)
            
            # Check for game commands
            for game_key in self.mini_games:
                if game_key in message.lower():
                    return self.mini_games[game_key](thread_id, None)
            
            # Check if already in a game
            if thread_id in self.game_states:
                game = self.game_states[thread_id]["game"]
                if game == "emoji":
                    return self.emoji_game(thread_id, message)
                elif game == "math":
                    return self.quick_math(thread_id, message)
                elif game == "guess":
                    return self.number_guess(thread_id, message)
            
            # Build conversation history
            messages = [{"role": "system", "content": self.personality}]
            
            if thread_id in self.conversations:
                for msg in self.conversations[thread_id][-6:]:  # Last 6 messages only
                    messages.append({
                        "role": "assistant" if msg["role"] == "bot" else "user",
                        "content": msg["content"]
                    })
            
            messages.append({"role": "user", "content": message})
            
            # Generate response
            response = self.ai_client.chat.completions.create(
                messages=messages,
                max_tokens=60,  # Keep it short
                temperature=0.9,
                model=self.azure_deployment,
                frequency_penalty=0.5,
                presence_penalty=0.5
            )
            
            text = response.choices[0].message.content
            
            # Occasionally throw in a random game (20% chance)
            if random.random() < 0.2 and thread_id not in self.game_states:
                game_prompt = random.choice([
                    "\n\nbtw, emoji game? 🎮",
                    "\n\nquick math? ⚡",
                    "\n\nvibe check? ✨",
                    "\n\nbet you can't guess my number 🎲"
                ])
                text += game_prompt
            
            return text if text else "..." 
            
        except Exception as e:
            logger.error(f"Gen failed: {e}")
            return random.choice(["bruh my brain glitched 🤖", "wait what? say that again", "...error 404: brain not found"])
    
    def process_message(self, thread_id: str, message_obj):
        """Process incoming message"""
        try:
            text = (message_obj.text or "").strip()
            lower = text.lower()
            
            # Activation
            if self.activate_passcode in lower:
                self.active_threads[thread_id] = True
                greetings = [
                    "yooo what's good! 🔥 ready for chaos?",
                    "alter ego activated 😈 let's get wild",
                    "sup! game? roast? wisdom? or just vibes?",
                    "the better harsha has arrived 💫",
                    "hey hey! what trouble we causing today?"
                ]
                response = random.choice(greetings)
                self.ig_client.direct_send(response, thread_ids=[thread_id])
                logger.info(f"Activated: {thread_id}")
                return
            
            # Deactivation
            if self.deactivate_passcode in lower:
                if thread_id in self.active_threads:
                    del self.active_threads[thread_id]
                    if thread_id in self.conversations:
                        del self.conversations[thread_id]
                    if thread_id in self.game_states:
                        del self.game_states[thread_id]
                    
                    goodbyes = [
                        "aight peace out ✌️ stay legendary",
                        "catch you on the flip side 🌊",
                        "gone but never forgotten 👻",
                        "later! keep being awesome 💫",
                        "*disappears in style* 😎"
                    ]
                    self.ig_client.direct_send(random.choice(goodbyes), thread_ids=[thread_id])
                    logger.info(f"Deactivated: {thread_id}")
                return
            
            # Process if active
            if self.active_threads.get(thread_id):
                # Save conversation
                if thread_id not in self.conversations:
                    self.conversations[thread_id] = []
                
                self.conversations[thread_id].append({"role": "user", "content": text})
                
                # Generate and send response
                response = self.generate_response(text, thread_id)
                
                # Simulate quick typing (0.5-2 sec)
                time.sleep(min(len(response) / 50, 2))
                
                self.ig_client.direct_send(response, thread_ids=[thread_id])
                
                self.conversations[thread_id].append({"role": "bot", "content": response})
                
                # Keep conversation size manageable
                if len(self.conversations[thread_id]) > 20:
                    self.conversations[thread_id] = self.conversations[thread_id][-10:]
                
                logger.info(f"Replied to {thread_id}: {response[:30]}...")
                
        except Exception as e:
            logger.error(f"Process error: {e}")
    
    def run(self):
        """Main loop"""
        logger.info("Harsha's Alter Ego is LIVE! 🚀")
        logger.info(f"Say '{self.activate_passcode}' to activate")
        
        processed = set()
        
        while True:
            try:
                threads = self.ig_client.direct_threads(amount=20, selected_filter="unread")
                
                for thread in threads:
                    thread_id = thread.id
                    messages = self.ig_client.direct_messages(thread_id, amount=10)
                    
                    for msg in reversed(messages):
                        msg_id = f"{thread_id}_{msg.id}"
                        
                        if msg_id in processed:
                            continue
                        
                        processed.add(msg_id)
                        
                        # Skip own messages and non-text
                        if msg.user_id == self.ig_client.user_id:
                            logger.debug(f"Skipping own message")
                            continue
                        
                        if not msg.text:
                            logger.debug(f"Skipping non-text message")
                            continue
                        
                        logger.info(f"Found message: '{msg.text[:50]}' from user {msg.user_id}")
                        
                        # Mark as seen
                        try:
                            self.ig_client.direct_message_seen(thread_id, msg.id)
                        except:
                            pass
                        
                        # Process
                        self.process_message(thread_id, msg)
                        
                        # Manage memory
                        if len(processed) > 500:
                            processed = set(list(processed)[-250:])
                
                time.sleep(15)  # Poll every 15 seconds
                
            except Exception as e:
                logger.error(f"Loop error: {e}")
                time.sleep(30)

def main():
    try:
        bot = HarshaAlterEgo()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Shut down by user")
    except Exception as e:
        logger.error(f"Fatal: {e}")

if __name__ == "__main__":
    main()