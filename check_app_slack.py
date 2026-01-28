
try:
    import app_slack
    print("✅ app_slack imported successfully")
except ImportError as e:
    print(f"❌ ImportError: {e}")
except SyntaxError as e:
    print(f"❌ SyntaxError: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
