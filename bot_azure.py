#!/usr/bin/env python3
"""
Instagram Alter Ego Bot - Using direct Azure OpenAI client
"""

import os
import time
import logging
import json
from datetime import datetime
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

class InstagramAlterEgoBot:
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
        self.max_history_length = 10
        
        # Instagram client
        self.instagram_client = None
        
        # Azure OpenAI client
        self.openai_client = None
        
        # Personality
        self.alter_ego_personality = os.getenv("ALTER_EGO_PERSONALITY", """
        You are my alter ego: a witty, adventurous version of myself who loves sci-fi and puns.
        Keep responses conversational, fun, and under 500 characters for Instagram.
        Never reveal you're an AI. Act as a human friend.
        """).strip()
        
        logger.info("Initializing Instagram Alter Ego Bot...")
        
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
    
    def _get_conversation_messages(self, thread_id: str) -> List[Dict]:
        """Get conversation history formatted for OpenAI"""
        messages = [
            {
                "role": "system",
                "content": self.alter_ego_personality
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
        """Generate AI response using Azure OpenAI"""
        try:
            # Get conversation history
            messages = self._get_conversation_messages(thread_id)
            
            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Generate response
            response = self.openai_client.chat.completions.create(
                messages=messages,
                max_tokens=200,  # Keep responses short for Instagram
                temperature=0.8,
                top_p=0.9,
                model=self.azure_deployment
            )
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Handle None response
            if response_text is None:
                logger.warning("Azure OpenAI returned empty response")
                return "Hmm, let me think about that... Can you rephrase?"
            
            # Ensure response fits Instagram's character limit
            if len(response_text) > 1000:
                response_text = response_text[:997] + "..."
            
            return response_text
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return "Sorry, I'm having trouble responding right now. Try again later!"
    
    def process_message(self, thread_id: str, message_obj):
        """Process a single message"""
        try:
            msg_text = (message_obj.text or "").strip()
            msg_lower = msg_text.lower()
            
            logger.debug(f"Processing message from thread {thread_id}: {msg_text[:50]}...")
            
            # Check for activation
            if self.activate_passcode.lower() in msg_lower:
                self.activated_threads[thread_id] = True
                response = "🤖 Alter ego activated! I'm ready to chat with my enhanced personality. What's on your mind?"
                self.instagram_client.direct_send(response, thread_ids=[thread_id])
                logger.info(f"Activated thread {thread_id}")
                return
            
            # Check for deactivation
            if self.deactivate_passcode.lower() in msg_lower:
                if thread_id in self.activated_threads:
                    self.activated_threads[thread_id] = False
                    response = "👋 Alter ego deactivated. Back to normal mode. See you later!"
                    self.instagram_client.direct_send(response, thread_ids=[thread_id])
                    # Clear conversation history for this thread
                    if thread_id in self.conversation_history:
                        del self.conversation_history[thread_id]
                    logger.info(f"Deactivated thread {thread_id}")
                return
            
            # Process if activated
            if self.activated_threads.get(thread_id, False):
                # Save user message
                self._save_conversation(thread_id, "User", msg_text)
                
                # Generate and send response
                response = self._generate_response(msg_text, thread_id)
                self.instagram_client.direct_send(response, thread_ids=[thread_id])
                
                # Save bot response
                self._save_conversation(thread_id, "AlterEgo", response)
                
                logger.info(f"Sent response to thread {thread_id}: {response[:50]}...")
                
        except Exception as e:
            logger.error(f"Error processing message in thread {thread_id}: {e}")
    
    def run(self, poll_interval: int = 30):
        """Main bot loop"""
        logger.info("Starting Instagram Alter Ego Bot...")
        logger.info(f"Bot username: {self.username}")
        logger.info(f"Polling interval: {poll_interval} seconds")
        logger.info(f"Activate with: {self.activate_passcode}")
        logger.info(f"Deactivate with: {self.deactivate_passcode}")
        
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
        
        # Create a sample .env file if it doesn't exist
        if not os.path.exists('.env'):
            logger.info("Creating sample .env file...")
            with open('.env', 'w') as f:
                f.write("""# Instagram Credentials
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_api_key
AZURE_ENDPOINT=https://harsh-mdpv63be-eastus2.cognitiveservices.azure.com/
AZURE_DEPLOYMENT=gpt-5-chat
AZURE_API_VERSION=2024-12-01-preview

# Bot Configuration
ACTIVATE_PASSCODE=activate_alter_ego
DEACTIVATE_PASSCODE=deactivate_alter_ego

# Alter Ego Personality
ALTER_EGO_PERSONALITY="You are my alter ego: a witty, adventurous version of myself who loves sci-fi and puns. Keep responses conversational, fun, and under 500 characters for Instagram. Never reveal you're an AI."
""")
            logger.info("Sample .env file created. Please edit it with your credentials.")
        return
    
    # Create and run bot
    try:
        logger.info("Starting bot...")
        bot = InstagramAlterEgoBot()
        bot.run(poll_interval=30)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()