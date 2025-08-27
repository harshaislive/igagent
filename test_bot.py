import os
import logging
from dotenv import load_dotenv
from instagrapi import Client
from autogen import ConversableAgent, UserProxyAgent

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    # Test Instagram client
    print("Testing Instagram client...")
    ig_client = Client()
    print("Instagram client created successfully")
    
    # Test AutoGen setup
    print("\nTesting AutoGen agents...")
    config_list = [
        {
            "model": "gpt-5-chat",
            "api_key": os.getenv("AZURE_OPENAI_API_KEY", "test_key"),
            "base_url": "https://harsh-mdpv63be-eastus2.cognitiveservices.azure.com/",
            "api_type": "azure",
            "api_version": "2025-04-01-preview"
        }
    ]
    
    alter_ego_agent = ConversableAgent(
        name="AlterEgo",
        system_message="You are a helpful assistant",
        llm_config={"config_list": config_list},
    )
    print("Alter ego agent created successfully")
    
    user_proxy = UserProxyAgent(
        name="User",
        human_input_mode="NEVER",
        code_execution_config=False,
    )
    print("User proxy created successfully")
    
    print("\nAll components initialized successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()