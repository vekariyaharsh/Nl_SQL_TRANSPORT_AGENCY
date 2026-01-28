
try:
    print("Importing langchain.chat_models...")
    from langchain.chat_models import ChatOpenAI
    print("✅ langchain.chat_models imported successfully")
except Exception as e:
    print(f"❌ Failed to import langchain.chat_models: {e}")

try:
    print("Importing langchain_community.chat_models...")
    from langchain_community.chat_models import ChatOpenAI
    print("✅ langchain_community.chat_models imported successfully")
except Exception as e:
    print(f"❌ Failed to import langchain_community.chat_models: {e}")
