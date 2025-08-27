import os
from dotenv import load_dotenv
from autogen import ConversableAgent, UserProxyAgent

load_dotenv()

config_list = [
    {
        "model": "gpt-5-chat",
        "api_key": os.getenv("AZURE_OPENAI_API_KEY", "test_key"),
        "base_url": "https://harsh-mdpv63be-eastus2.cognitiveservices.azure.com/",
        "api_type": "azure",
        "api_version": "2025-04-01-preview"
    }
]

print("Creating agent...")
alter_ego_agent = ConversableAgent(
    name="AlterEgo",
    system_message="You are a helpful assistant",
    llm_config={"config_list": config_list},
)
print("Agent created successfully!")