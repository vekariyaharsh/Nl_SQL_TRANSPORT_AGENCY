
import os
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from nl_to_sql.config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_slack():
    print("-" * 50)
    print("Testing Slack Connection")
    print("-" * 50)
    
    token = Config.SLACK_BOT_TOKEN
    channel = Config.SLACK_CHANNEL_ID
    
    print(f"Token present: {'Yes' if token else 'No'}")
    print(f"Target Channel: {channel}")
    
    if not token:
        print("❌ Error: SLACK_BOT_TOKEN not set in environment or .env")
        return
        
    client = WebClient(token=token)
    
    try:
        print(f"Attempting to post to {channel}...")
        response = client.chat_postMessage(
            channel=channel,
            text="👋 Hello! This is a test message from the NL-to-SQL Pipeline."
        )
        print("✅ Message sent successfully!")
        print(f"Timestamp: {response['ts']}")
        
    except SlackApiError as e:
        print(f"❌ Slack API Error: {e.response['error']}")
        if e.response['error'] == 'channel_not_found':
            print(f"Tip: Ensure the bot is added to the channel {channel}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        Config.validate()
    except:
        pass # Ignore other config errors for this test
    test_slack()
