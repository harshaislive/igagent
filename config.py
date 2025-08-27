import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class BotConfig:
    """Configuration for Instagram Alter Ego Bot"""
    
    # Instagram Settings
    instagram_username: str
    instagram_password: str
    
    # Azure OpenAI Settings
    azure_api_key: str
    azure_endpoint: str = "https://harsh-mdpv63be-eastus2.cognitiveservices.azure.com/"
    azure_deployment: str = "gpt-5-chat"
    azure_api_version: str = "2025-04-01-preview"
    
    # Bot Settings
    activate_passcode: str = "activate_alter_ego"
    deactivate_passcode: str = "deactivate_alter_ego"
    poll_interval: int = 30  # seconds
    max_history_length: int = 10
    max_response_length: int = 1000
    
    # Personality Settings
    alter_ego_personality: str = """
    You are my alter ego: a witty, adventurous version of myself who loves sci-fi and puns.
    Keep responses conversational, fun, and under 500 characters for Instagram.
    Never reveal you're an AI. Act as a human friend.
    """
    
    # Safety Settings
    rate_limit_delay: int = 5  # seconds between API calls
    max_threads_per_poll: int = 20
    max_messages_per_thread: int = 10
    
    @classmethod
    def from_env(cls) -> 'BotConfig':
        """Load configuration from environment variables"""
        return cls(
            instagram_username=os.getenv("INSTAGRAM_USERNAME", ""),
            instagram_password=os.getenv("INSTAGRAM_PASSWORD", ""),
            azure_api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            azure_endpoint=os.getenv("AZURE_ENDPOINT", cls.azure_endpoint),
            azure_deployment=os.getenv("AZURE_DEPLOYMENT", cls.azure_deployment),
            azure_api_version=os.getenv("AZURE_API_VERSION", cls.azure_api_version),
            activate_passcode=os.getenv("ACTIVATE_PASSCODE", cls.activate_passcode),
            deactivate_passcode=os.getenv("DEACTIVATE_PASSCODE", cls.deactivate_passcode),
            poll_interval=int(os.getenv("POLL_INTERVAL", str(cls.poll_interval))),
            max_history_length=int(os.getenv("MAX_HISTORY_LENGTH", str(cls.max_history_length))),
            max_response_length=int(os.getenv("MAX_RESPONSE_LENGTH", str(cls.max_response_length))),
            alter_ego_personality=os.getenv("ALTER_EGO_PERSONALITY", cls.alter_ego_personality),
            rate_limit_delay=int(os.getenv("RATE_LIMIT_DELAY", str(cls.rate_limit_delay))),
            max_threads_per_poll=int(os.getenv("MAX_THREADS_PER_POLL", str(cls.max_threads_per_poll))),
            max_messages_per_thread=int(os.getenv("MAX_MESSAGES_PER_THREAD", str(cls.max_messages_per_thread))),
        )
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not self.instagram_username:
            errors.append("INSTAGRAM_USERNAME is required")
        if not self.instagram_password:
            errors.append("INSTAGRAM_PASSWORD is required")
        if not self.azure_api_key:
            errors.append("AZURE_OPENAI_API_KEY is required")
        
        if self.poll_interval < 10:
            errors.append("POLL_INTERVAL should be at least 10 seconds to avoid rate limiting")
        
        if self.max_response_length > 2000:
            errors.append("MAX_RESPONSE_LENGTH should not exceed 2000 characters for Instagram")
        
        return errors