
try:
    print("Importing openai...")
    from openai import OpenAI
    print("✅ openai imported successfully")
except Exception as e:
    print(f"❌ Failed to import openai: {e}")
