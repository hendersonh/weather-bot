import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import vertexai
from vertexai.preview import reasoning_engines
from vertexai import agent_engines

#from root_agent.agent import root_agent  # Import the root_agent directly
# After (package-level import)
from root_agent import root_agent
# Project setup
PROJECT_ID = "chatbot-8ebb8"
LOCATION = "us-central1"
STAGING_BUCKET = f"gs://{PROJECT_ID}-agent-staging"

print(f"Initializing Vertex AI for project '{PROJECT_ID}' in location '{LOCATION}'...")
vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET
)
print("Vertex AI initialized successfully.")

print("Creating ADK App...")
app = reasoning_engines.AdkApp(
    agent=root_agent,  # Use root_agent directly
    enable_tracing=True
)
print("ADK App created successfully.")

# !!! IMPORTANT: Replace with your actual OpenWeather API key below !!!
OPENWEATHER_API_KEY_VALUE = "88688d9057158299370fa79d5dc2a854"

print("Deploying agent to Vertex AI Agent Engine. This may take a few minutes...")

# Define environment variables for the deployed agent
env_vars_for_agent = {
    "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY_VALUE
}

agent_engine = agent_engines.create(
    agent_engine=app,
    requirements=[
        "google-cloud-aiplatform[adk,agent_engines]",
        "google-adk",
        "requests",
        "python-dotenv",
        "geopy",
        "timezonefinder",
    ],
    extra_packages=["root_agent"],  # Explicitly bundle local module
    env_vars=env_vars_for_agent  # Pass the environment variables here
)
print("Agent deployment initiated successfully.")
print(f"Deployed Agent Engine resource name: {agent_engine.resource_name}")

# Test the deployed agent
print("\nTesting the deployed agent...")
test_user_id = "test-user-1"
session = agent_engine.create_session(user_id=test_user_id)

print("Streaming response:")
for event in agent_engine.stream_query(
    message="What's the weather in Toronto?",
    user_id=test_user_id,
    session_id=session["id"]
):
    print(event)