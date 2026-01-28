
try:
    print("Importing langchain_openai...")
    from langchain_openai import ChatOpenAI
    print("✅ langchain_openai imported successfully")
except Exception as e:
    print(f"❌ Failed to import langchain_openai: {e}")

try:
    print("Importing langchain.prompts...")
    from langchain.prompts import ChatPromptTemplate
    print("✅ langchain.prompts imported successfully")
except Exception as e:
    print(f"❌ Failed to import langchain.prompts: {e}")
