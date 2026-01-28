
try:
    import flask
    print("✅ Flask is installed")
except ImportError:
    print("❌ Flask is NOT installed")

try:
    import slack_sdk
    print("✅ slack_sdk is installed")
except ImportError:
    print("❌ slack_sdk is NOT installed")

try:
    from langgraph.checkpoint.memory import MemorySaver
    print("✅ langgraph.checkpoint.memory.MemorySaver found")
except ImportError:
    print("❌ MemorySaver import failed (check langgraph version)")
