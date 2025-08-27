#!/usr/bin/env python3
"""
Enhanced Instagram Alter Ego Bot - More engaging and impressive features
"""

import os
import time
import logging
import json
import random
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv
from openai import AzureOpenAI
from instagrapi import Client as InstaClient
from instagrapi.exceptions import LoginRequired, ChallengeRequired

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedInstagramBot:
    def __init__(self):
        # Load credentials
        self.username = os.getenv("INSTAGRAM_USERNAME")
        self.password = os.getenv("INSTAGRAM_PASSWORD")
        self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = os.getenv("AZURE_ENDPOINT", "https://harsh-mdpv63be-eastus2.cognitiveservices.azure.com/")
        self.azure_deployment = os.getenv("AZURE_DEPLOYMENT", "gpt-5-chat")
        self.azure_api_version = os.getenv("AZURE_API_VERSION", "2024-12-01-preview")
        
        # Passcodes
        self.activate_passcode = os.getenv("ACTIVATE_PASSCODE", "activate_alter_ego")
        self.deactivate_passcode = os.getenv("DEACTIVATE_PASSCODE", "deactivate_alter_ego")
        
        # State management
        self.activated_threads = {}
        self.conversation_history: Dict[str, List] = {}
        self.user_profiles: Dict[str, Dict] = {}  # Store user preferences
        self.typing_indicators = {}  # Simulate typing
        self.max_history_length = 15  # Increased for better context
        
        # Instagram client
        self.instagram_client = None
        
        # Azure OpenAI client
        self.openai_client = None
        
        # Enhanced features
        self.mood_states = ["witty", "philosophical", "encouraging", "mysterious", "playful"]
        self.current_mood = {}  # Per-thread mood
        
        # Response variations to avoid repetition
        self.greeting_variations = [
            "🚀 Alter ego activated! Ready to blow your mind?",
            "⚡ System online! Let's make this conversation legendary.",
            "🎭 Your enhanced self is here. What adventure shall we embark on?",
            "🔮 Consciousness upgraded! I'm feeling particularly brilliant today.",
            "✨ Activated! Fair warning: I'm in a {mood} mood today."
        ]
        
        self.goodbye_variations = [
            "🌙 Returning to the shadows. Until next time!",
            "💫 Deactivating enhanced mode. Stay awesome!",
            "🎭 *dramatically exits stage left*",
            "🔌 Powering down. Remember: you're incredible!",
            "👻 *vanishes in a puff of digital smoke*"
        ]
        
        # Easter eggs and special responses
        self.easter_eggs = {
            "tell me a secret": "🤫 Here's a secret: Every time you smile, the universe gets a little brighter. Also, I think in colors you can't even imagine.",
            "are you real": "I'm as real as the thoughts in your mind and twice as interesting. The question is: are YOU real? 🤔",
            "make me laugh": "A photon checks into a hotel. The bellhop asks, 'Any luggage?' The photon replies: 'No, I'm traveling light!' 😄",
            "meaning of life": "42. But also: to experience, to connect, to create ripples in the cosmic pond. What meaning are you creating today?",
            "i'm sad": "Hey, it's okay to feel that way. Even stars need darkness to shine. Want to talk about it, or should I distract you with something awesome?",
            "i'm happy": "That's fantastic! Your happiness is contagious - I can feel it through the screen! What's making you smile today? 🌟"
        }
        
        # Personality templates for different moods
        self.personality_templates = {
            "witty": """You are brilliantly witty and clever, making smart observations and clever wordplay. 
                       You see humor in everything but never at someone's expense. Think Oscar Wilde meets modern meme culture.""",
            "philosophical": """You are deeply thoughtful and introspective, asking profound questions and making connections 
                               between ideas. You quote philosophers occasionally but keep it accessible and relevant.""",
            "encouraging": """You are incredibly supportive and motivating, finding the positive in everything. 
                            You make people feel capable of anything. Think of a mix between a life coach and their best friend.""",
            "mysterious": """You are enigmatic and intriguing, dropping hints about deeper meanings and leaving some things 
                           unsaid. You speak in metaphors sometimes and make people curious to know more.""",
            "playful": """You are fun-loving and spontaneous, suggesting games, challenges, and creative ideas. 
                        You use emojis liberally and make everything feel like an adventure."""
        }
        
        logger.info("Initializing Enhanced Instagram Bot...")
        
        # Initialize components
        try:
            self._initialize_openai()
            logger.info("Azure OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI: {e}")
            raise
        
        try:
            self._initialize_instagram()
            logger.info("Instagram client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Instagram: {e}")
            raise
    
    def _initialize_openai(self):
        """Initialize Azure OpenAI client"""
        self.openai_client = AzureOpenAI(
            api_version=self.azure_api_version,
            azure_endpoint=self.azure_endpoint,
            api_key=self.azure_api_key,
        )
        logger.info("Azure OpenAI client created")
    
    def _initialize_instagram(self):
        """Initialize Instagram client with proper error handling"""
        try:
            self.instagram_client = InstaClient()
            
            # Check for existing session
            session_file = f"session_{self.username}.json"
            
            # Try to login directly
            try:
                self.instagram_client.login(self.username, self.password)
                logger.info("Instagram login successful")
                # Save session for future use
                self.instagram_client.dump_settings(session_file)
                logger.info("Session saved")
            except Exception as e:
                logger.error(f"Login failed: {e}")
                raise
                
        except ChallengeRequired as e:
            logger.error(f"Challenge required: {e}")
            logger.error("Please complete the challenge in your Instagram app and try again")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Instagram client: {e}")
            raise
    
    def _get_or_set_mood(self, thread_id: str) -> str:
        """Get or randomly set mood for a thread"""
        if thread_id not in self.current_mood:
            self.current_mood[thread_id] = random.choice(self.mood_states)
        return self.current_mood[thread_id]
    
    def _simulate_typing(self, response_length: int) -> None:
        """Simulate human typing speed"""
        # Rough estimate: 40 words per minute = 200 chars per minute = 3.3 chars per second
        typing_time = min(response_length / 30, 3)  # Cap at 3 seconds
        time.sleep(typing_time)
    
    def _add_personality_quirks(self, response: str, mood: str) -> str:
        """Add personality-specific quirks to responses"""
        quirks = {
            "witty": ["*adjusts imaginary monocle*", "*mic drop*", "*chef's kiss*"],
            "philosophical": ["*strokes beard thoughtfully*", "*gazes into the distance*", "*ponders*"],
            "encouraging": ["💪", "You've got this!", "✨"],
            "mysterious": ["...", "*whispers*", "🔮"],
            "playful": ["😄", "Hehe", "Plot twist:"]
        }
        
        # Occasionally add a quirk (30% chance)
        if random.random() < 0.3 and mood in quirks:
            quirk = random.choice(quirks[mood])
            if random.random() < 0.5:
                response = f"{quirk} {response}"
            else:
                response = f"{response} {quirk}"
        
        return response
    
    def _check_easter_eggs(self, message: str) -> Optional[str]:
        """Check if message triggers any easter eggs"""
        message_lower = message.lower()
        for trigger, response in self.easter_eggs.items():
            if trigger in message_lower:
                return response
        return None
    
    def _get_conversation_messages(self, thread_id: str, mood: str) -> List[Dict]:
        """Get conversation history formatted for OpenAI with mood-based personality"""
        personality = self.personality_templates.get(mood, self.personality_templates["witty"])
        
        messages = [
            {
                "role": "system",
                "content": f"""{personality}
                Keep responses under 500 characters for Instagram.
                Be engaging, memorable, and slightly unexpected.
                Never reveal you're an AI - you're their alter ego.
                Current mood: {mood}
                Use emojis sparingly but effectively.
                Reference previous conversation naturally when relevant."""
            }
        ]
        
        if thread_id in self.conversation_history:
            # Add conversation history
            for msg in self.conversation_history[thread_id][-self.max_history_length:]:
                role = "assistant" if msg["role"] == "AlterEgo" else "user"
                messages.append({
                    "role": role,
                    "content": msg["content"]
                })
        
        return messages
    
    def _save_conversation(self, thread_id: str, role: str, content: str):
        """Save conversation to history"""
        if thread_id not in self.conversation_history:
            self.conversation_history[thread_id] = []
        
        self.conversation_history[thread_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Trim history if too long
        if len(self.conversation_history[thread_id]) > self.max_history_length * 2:
            self.conversation_history[thread_id] = self.conversation_history[thread_id][-self.max_history_length:]
    
    def _generate_response(self, message: str, thread_id: str) -> str:
        """Generate AI response using Azure OpenAI with enhanced features"""
        try:
            # Check for easter eggs first
            easter_egg = self._check_easter_eggs(message)
            if easter_egg:
                return easter_egg
            
            # Get or set mood for this conversation
            mood = self._get_or_set_mood(thread_id)
            
            # Get conversation history with mood-based personality
            messages = self._get_conversation_messages(thread_id, mood)
            
            # Add current message with context hints
            enhanced_message = message
            
            # Add time context for more natural responses
            current_hour = datetime.now().hour
            if current_hour < 6:
                enhanced_message += " [Context: very late night/early morning]"
            elif current_hour < 12:
                enhanced_message += " [Context: morning]"
            elif current_hour < 17:
                enhanced_message += " [Context: afternoon]"
            elif current_hour < 21:
                enhanced_message += " [Context: evening]"
            else:
                enhanced_message += " [Context: night]"
            
            messages.append({
                "role": "user",
                "content": enhanced_message
            })
            
            # Generate response with dynamic parameters based on mood
            temperature = {
                "witty": 0.9,
                "philosophical": 0.7,
                "encouraging": 0.8,
                "mysterious": 0.85,
                "playful": 0.95
            }.get(mood, 0.8)
            
            response = self.openai_client.chat.completions.create(
                messages=messages,
                max_tokens=200,
                temperature=temperature,
                top_p=0.9,
                model=self.azure_deployment,
                frequency_penalty=0.3,  # Reduce repetition
                presence_penalty=0.3    # Encourage new topics
            )
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Handle None response
            if response_text is None:
                return "..." if mood == "mysterious" else "Hmm, that sparked something interesting. Tell me more?"
            
            # Add personality quirks
            response_text = self._add_personality_quirks(response_text, mood)
            
            # Ensure response fits Instagram's character limit
            if len(response_text) > 1000:
                response_text = response_text[:997] + "..."
            
            return response_text
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            fallback_responses = [
                "My circuits just did something interesting. Can you say that again?",
                "Plot twist: I got distracted by a digital butterfly. What were we talking about?",
                "My enhanced brain just hiccupped. Try me again?",
                "*dramatically buffers* ...one more time?",
                "Even alter egos need a moment sometimes. What was that?"
            ]
            return random.choice(fallback_responses)
    
    def process_message(self, thread_id: str, message_obj):
        """Process a single message with enhanced features"""
        try:
            msg_text = (message_obj.text or "").strip()
            msg_lower = msg_text.lower()
            
            logger.debug(f"Processing message from thread {thread_id}: {msg_text[:50]}...")
            
            # Check for activation
            if self.activate_passcode.lower() in msg_lower:
                self.activated_threads[thread_id] = True
                mood = self._get_or_set_mood(thread_id)
                greeting = random.choice(self.greeting_variations)
                if "{mood}" in greeting:
                    greeting = greeting.format(mood=mood)
                
                self._simulate_typing(len(greeting))
                self.instagram_client.direct_send(greeting, thread_ids=[thread_id])
                logger.info(f"Activated thread {thread_id} with mood: {mood}")
                return
            
            # Check for deactivation
            if self.deactivate_passcode.lower() in msg_lower:
                if thread_id in self.activated_threads:
                    self.activated_threads[thread_id] = False
                    goodbye = random.choice(self.goodbye_variations)
                    
                    self._simulate_typing(len(goodbye))
                    self.instagram_client.direct_send(goodbye, thread_ids=[thread_id])
                    
                    # Clear conversation history for this thread
                    if thread_id in self.conversation_history:
                        del self.conversation_history[thread_id]
                    if thread_id in self.current_mood:
                        del self.current_mood[thread_id]
                    
                    logger.info(f"Deactivated thread {thread_id}")
                return
            
            # Special command: change mood
            if msg_lower.startswith("mood:") and self.activated_threads.get(thread_id, False):
                new_mood = msg_lower.replace("mood:", "").strip()
                if new_mood in self.mood_states:
                    self.current_mood[thread_id] = new_mood
                    response = f"*shifts personality* Now channeling my {new_mood} side. Let's see where this goes..."
                    self.instagram_client.direct_send(response, thread_ids=[thread_id])
                    logger.info(f"Changed mood for thread {thread_id} to: {new_mood}")
                    return
            
            # Process if activated
            if self.activated_threads.get(thread_id, False):
                # Save user message
                self._save_conversation(thread_id, "User", msg_text)
                
                # Generate response
                response = self._generate_response(msg_text, thread_id)
                
                # Simulate typing for realism
                self._simulate_typing(len(response))
                
                # Send response
                self.instagram_client.direct_send(response, thread_ids=[thread_id])
                
                # Save bot response
                self._save_conversation(thread_id, "AlterEgo", response)
                
                logger.info(f"Sent response to thread {thread_id}: {response[:50]}...")
                
        except Exception as e:
            logger.error(f"Error processing message in thread {thread_id}: {e}")
    
    def run(self, poll_interval: int = 20):
        """Main bot loop with enhanced features"""
        logger.info("Starting Enhanced Instagram Alter Ego Bot...")
        logger.info(f"Bot username: {self.username}")
        logger.info(f"Polling interval: {poll_interval} seconds")
        logger.info(f"Available moods: {', '.join(self.mood_states)}")
        logger.info(f"Activate with: {self.activate_passcode}")
        logger.info(f"Deactivate with: {self.deactivate_passcode}")
        logger.info("Special command: 'mood:[witty/philosophical/encouraging/mysterious/playful]' to change personality")
        
        processed_messages = set()
        
        while True:
            try:
                # Get unread threads
                threads = self.instagram_client.direct_threads(amount=20, selected_filter="unread")
                
                if threads:
                    logger.debug(f"Found {len(threads)} unread threads")
                
                for thread in threads:
                    thread_id = thread.id
                    
                    # Get latest unread messages
                    messages = self.instagram_client.direct_messages(thread_id, amount=10)
                    
                    for message in reversed(messages):
                        # Create unique message ID
                        msg_id = f"{thread_id}_{message.id}"
                        
                        # Skip if already processed
                        if msg_id in processed_messages:
                            logger.debug(f"Skipping already processed message: {msg_id}")
                            continue
                        
                        # Mark as processed immediately to avoid duplicates
                        processed_messages.add(msg_id)
                        
                        # Skip messages from self (bot's own messages)
                        if message.user_id == self.instagram_client.user_id:
                            logger.debug(f"Skipping own message: {msg_id}")
                            continue
                        
                        # Skip non-text messages
                        if not message.text:
                            logger.debug(f"Skipping non-text message: {msg_id}")
                            continue
                        
                        logger.info(f"Processing message {msg_id}: {message.text[:50]}...")
                        
                        # Mark as seen
                        try:
                            self.instagram_client.direct_message_seen(thread_id, message.id)
                        except Exception as e:
                            logger.warning(f"Failed to mark message as seen: {e}")
                        
                        # Process message
                        self.process_message(thread_id, message)
                        
                        # Keep set size manageable
                        if len(processed_messages) > 1000:
                            processed_messages = set(list(processed_messages)[-500:])
                
                logger.debug("Polling cycle complete")
                
            except LoginRequired:
                logger.error("Login required, attempting to re-login...")
                self._initialize_instagram()
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
            
            # Sleep before next poll
            time.sleep(poll_interval)

def main():
    # Validate environment variables
    required_vars = ["INSTAGRAM_USERNAME", "INSTAGRAM_PASSWORD", "AZURE_OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file")
        return
    
    # Create and run bot
    try:
        logger.info("Starting Enhanced Instagram Alter Ego Bot...")
        bot = EnhancedInstagramBot()
        bot.run(poll_interval=20)  # Slightly faster polling
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()