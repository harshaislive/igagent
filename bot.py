import os
import time
import logging
import json
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv
# Import autogen first to avoid namespace conflicts
from autogen import ConversableAgent, UserProxyAgent
# Then import instagrapi with alias to avoid conflicts
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
        self.azure_api_version = os.getenv("AZURE_API_VERSION", "2025-04-01-preview")
        
        # Passcodes
        self.activate_passcode = os.getenv("ACTIVATE_PASSCODE", "activate_alter_ego")
        self.deactivate_passcode = os.getenv("DEACTIVATE_PASSCODE", "deactivate_alter_ego")
        
        # State management
        self.activated_threads = {}
        self.conversation_history = {}
        self.max_history_length = 10
        
        # Instagram client
        self.client = None
        
        # AutoGen agents
        self.alter_ego_agent = None
        self.user_proxy = None
        
        # Initialize components
        self._initialize_instagram()
        self._initialize_agents()
    
    def _initialize_instagram(self):
        """Initialize Instagram client with proper error handling"""
        try:
            self.client = InstaClient()
            
            # Check for existing session
            session_file = f"session_{self.username}.json"
            if os.path.exists(session_file):
                try:
                    with open(session_file, 'r') as f:
                        settings = json.load(f)
                        # Remove proxies if present to avoid compatibility issues
                        if 'proxies' in settings:
                            del settings['proxies']
                        # Load cleaned settings
                        self.client.set_settings(settings)
                        self.client.login(self.username, self.password)
                        logger.info("Logged in using saved session")
                except Exception as e:
                    logger.warning(f"Session login failed: {e}")
                    # Remove corrupt session file
                    if os.path.exists(session_file):
                        os.remove(session_file)
                    self._fresh_login(session_file)
            else:
                self._fresh_login(session_file)
                
        except ChallengeRequired as e:
            logger.error(f"Challenge required: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Instagram client: {e}")
            raise
    
    def _fresh_login(self, session_file: str):
        """Perform fresh login and save session"""
        try:
            self.client.login(self.username, self.password)
            self.client.dump_settings(session_file)
            logger.info("Fresh login successful, session saved")
        except Exception as e:
            logger.error(f"Fresh login failed: {e}")
            raise
    
    def _initialize_agents(self):
        """Initialize AutoGen agents"""
        config_list = [
            {
                "model": self.azure_deployment,
                "api_key": self.azure_api_key,
                "base_url": self.azure_endpoint,
                "api_type": "azure",
                "api_version": self.azure_api_version
            }
        ]
        
        # Load custom personality from config
        alter_ego_personality = os.getenv("ALTER_EGO_PERSONALITY", """
        You are my alter ego: a witty, adventurous version of myself who loves sci-fi and puns.
        Keep responses conversational, fun, and under 500 characters for Instagram.
        Never reveal you're an AI. Act as a human friend.
        """)
        
        self.alter_ego_agent = ConversableAgent(
            name="AlterEgo",
            system_message=alter_ego_personality,
            llm_config={"config_list": config_list},
        )
        
        self.user_proxy = UserProxyAgent(
            name="User",
            human_input_mode="NEVER",
            code_execution_config=False,
        )
        
        logger.info("AutoGen agents initialized")
    
    def _get_conversation_context(self, thread_id: str) -> str:
        """Get conversation history for context"""
        if thread_id not in self.conversation_history:
            return ""
        
        history = self.conversation_history[thread_id][-self.max_history_length:]
        context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
        return f"Previous conversation:\n{context}\n\nNew message:"
    
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
        """Generate AI response with context"""
        try:
            context = self._get_conversation_context(thread_id)
            full_message = f"{context} {message}" if context else message
            
            # Generate response
            chat_result = self.user_proxy.initiate_chat(
                self.alter_ego_agent,
                message=full_message,
                max_turns=1,
                clear_history=True
            )
            
            # Extract response
            response = chat_result.chat_history[-1]["content"]
            
            # Ensure response fits Instagram's character limit
            if len(response) > 1000:
                response = response[:997] + "..."
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return "Sorry, I'm having trouble responding right now. Try again later!"
    
    def process_message(self, thread_id: str, message_obj):
        """Process a single message"""
        try:
            sender_id = message_obj.user_id
            msg_text = (message_obj.text or "").strip()
            msg_lower = msg_text.lower()
            
            # Check for activation
            if self.activate_passcode in msg_lower:
                self.activated_threads[thread_id] = True
                response = "🤖 Alter ego activated! I'm ready to chat with my enhanced personality. What's on your mind?"
                self.client.direct_send(response, thread_ids=[thread_id])
                logger.info(f"Activated thread {thread_id}")
                return
            
            # Check for deactivation
            if self.deactivate_passcode in msg_lower:
                if thread_id in self.activated_threads:
                    self.activated_threads[thread_id] = False
                    response = "👋 Alter ego deactivated. Back to normal mode. See you later!"
                    self.client.direct_send(response, thread_ids=[thread_id])
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
                self.client.direct_send(response, thread_ids=[thread_id])
                
                # Save bot response
                self._save_conversation(thread_id, "AlterEgo", response)
                
                logger.info(f"Sent response to thread {thread_id}")
                
        except Exception as e:
            logger.error(f"Error processing message in thread {thread_id}: {e}")
    
    def run(self, poll_interval: int = 30):
        """Main bot loop"""
        logger.info("Starting Instagram Alter Ego Bot...")
        
        while True:
            try:
                # Get unread threads
                threads = self.client.direct_threads(amount=20, selected_filter="unread")
                
                for thread in threads:
                    thread_id = thread.id
                    
                    # Get latest unread messages
                    messages = self.client.direct_messages(thread_id, amount=10)
                    
                    for message in reversed(messages):
                        # Skip if already seen or from self
                        if message.user_id == self.client.user_id:
                            continue
                        
                        # Mark as seen
                        try:
                            self.client.direct_message_seen(thread_id, message.id)
                        except:
                            pass
                        
                        # Process message
                        self.process_message(thread_id, message)
                
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
        bot = InstagramAlterEgoBot()
        bot.run(poll_interval=30)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()