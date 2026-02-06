"""
System Test script for Logistics SQL Pipeline
"""
import sys
import os
from colorama import init, Fore, Style

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Initialize colorama for colored output
init(autoreset=True)

def print_header(text):
    print("\n" + "="*80)
    print(f"{Fore.CYAN}{Style.BRIGHT}{text}")
    print("="*80)

def print_success(text):
    print(f"{Fore.GREEN}✅ {text}")

def print_error(text):
    print(f"{Fore.RED}❌ {text}")

def print_info(text):
    print(f"{Fore.BLUE}ℹ️  {text}")

def test_configuration():
    print_header("1. Testing Configuration")
    try:
        from nl_to_sql.config import Config
        print_info(f"Using Model: {Config.OPENAI_MODEL}")
        print_success("Configuration loaded successfully")
        return True
    except Exception as e:
        print_error(f"Configuration error: {e}")
        return False

def test_database_manager():
    print_header("2. Testing Database Manager (MySQL)")
    try:
        from nl_to_sql.database.database_manager import DatabaseManager
        from nl_to_sql.config import Config

        db = DatabaseManager()
        # Simple query to check connectivity
        results = db.execute_query("SELECT 1 as health")
        if results and results[0]['health'] == 1:
            print_success("MySQL connectivity verified via DatabaseManager")

            # Check schema loading
            from nl_to_sql.database.mysql_schema_loader import MySQLSchemaLoader
            loader = MySQLSchemaLoader(db)
            schema = loader.load_schema()
            print_info(f"Found {len(schema['tables'])} tables")
            return True
        return False
    except Exception as e:
        print_error(f"Database error: {e}")
        return False

def test_sql_examples():
    print_header("3. Testing Logistics SQL Examples")
    try:
        from nl_to_sql.utils.few_shot_examples_sql import LogisticsSQLExamples
        count = LogisticsSQLExamples.get_example_count()
        print_success(f"Loaded {count} logistics SQL examples")
        return True
    except Exception as e:
        print_error(f"SQL examples error: {e}")
        return False

def test_pipeline_import():
    print_header("4. Testing Pipeline Component Imports")
    try:
        from nl_to_sql.api.app import build_graph
        pipeline = build_graph()
        print_success("Pipeline graph built successfully")
        return True
    except Exception as e:
        print_error(f"Pipeline import error: {e}")
        return False

def run_all_tests():
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}{'='*80}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}🧪 Logistics SQL Pipeline - System Test")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}{'='*80}\n")

    results = {
        "Configuration": test_configuration(),
        "Database (MySQL)": test_database_manager(),
        "SQL Examples": test_sql_examples(),
        "Pipeline Import": test_pipeline_import()
    }

    print_header("Test Summary")
    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = f"{Fore.GREEN}✅ PASSED" if result else f"{Fore.RED}❌ FAILED"
        print(f"{test_name:.<40} {status}")

    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
