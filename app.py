"""
LangGraph NL-to-SQL Pipeline - Main Application

This application orchestrates a multi-stage workflow for converting natural language
questions to MySQL SQL queries with validation, correction, and execution.

Modes:
1. CLI Interactive: python app.py
2. CLI Single Query: python app.py -q "question"
3. Server/Slack:    python app.py --server
"""
import os
import sys
import uuid
import logging
import argparse
from typing import Literal, Dict, Any, Optional

from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from config import Config
from langgraph_schema import OverallState, create_initial_state

# Import the refactored MySQL-based nodes
from node_nl_to_query import nl_to_query_node
from node_query_validator import validate_query_node
from node_query_corrector import correct_query_node
from node_query_executor import execute_query_node

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# Core Pipeline Definition
# ==========================================

def route_after_validation(state: OverallState) -> Literal["execute", "correct", "end"]:
    """Routing logic after validation"""
    is_revalidation = state.get("corrected_query") is not None
    
    if is_revalidation:
        if state.get("final_validation_passed"):
            print("🎯 Final validation passed → Executing query")
            return "execute"
        else:
            iteration_count = state.get("iteration_count", 0)
            if iteration_count >= Config.MAX_CORRECTION_ITERATIONS:
                print(f"⚠️  Max iterations ({Config.MAX_CORRECTION_ITERATIONS}) reached → Ending")
                return "end"
            else:
                print("🔄 Final validation failed → Correcting again")
                return "correct"
    else:
        if state.get("validation_passed"):
            print("✅ Initial validation passed → Executing query")
            return "execute"
        else:
            print("🔧 Initial validation failed → Correcting query")
            return "correct"

def build_graph(checkpointer=None):
    """Build the LangGraph workflow"""
    workflow = StateGraph(OverallState)
    
    # Add nodes
    workflow.add_node("nl_to_sql", nl_to_query_node)
    workflow.add_node("validate_sql", validate_query_node)
    workflow.add_node("correct_sql", correct_query_node)
    workflow.add_node("execute_sql", execute_query_node)
    
    # Set entry point
    workflow.set_entry_point("nl_to_sql")
    
    # Add edges
    workflow.add_edge("nl_to_sql", "validate_sql")
    
    workflow.add_conditional_edges(
        "validate_sql",
        route_after_validation,
        {
            "execute": "execute_sql",
            "correct": "correct_sql",
            "end": END
        }
    )
    
    workflow.add_edge("correct_sql", "validate_sql")
    workflow.add_edge("execute_sql", END)
    
    # Compile
    return workflow.compile(checkpointer=checkpointer)

# ==========================================
# Flask / Slack Server Logic
# ==========================================

import threading

app = Flask(__name__)
slack_client = None # Initialized if token exists

def init_slack_client():
    global slack_client
    token = Config.SLACK_BOT_TOKEN
    if token:
        slack_client = WebClient(token=token)
        logger.info("✅ Slack client initialized")
    else:
        logger.warning("⚠️  SLACK_BOT_TOKEN not found - Slack messaging disabled")

def send_slack_message(channel, text, thread_ts=None):
    """Send message to Slack channel"""
    if not slack_client:
        return None
        
    try:
        response = slack_client.chat_postMessage(
            channel=channel,
            text=text,
            thread_ts=thread_ts
        )
        return response
    except Exception as e:
        logger.error(f"Error sending Slack message: {e}")
        return None

def format_response_for_slack(state: Dict[str, Any]) -> str:
    """Format results for Slack"""
    if state.get("execution_success"):
        result_data = state.get("execution_result", {})
        count = result_data.get("count", 0)
        formatted_rows = result_data.get("formatted", "")
        sql_query = state.get("corrected_query") or state.get("generated_query")
        
        response = f"*Query Executed Successfully* ✅\n"
        response += f"Found {count} results.\n\n"
        response += f"```sql\n{sql_query}\n```\n\n"
        response += f"*Results:*\n{formatted_rows}"
        return response
    elif state.get("error_message"):
        return f"❌ *Error Occurred:*\n{state['error_message']}"
    return "⚠️ Process incomplete or failed validation."

def process_pipeline_background(user_message, thread_id, channel_id, thread_ts):
    """Run pipeline in background thread"""
    logger.info(f"🧵 Starting background thread for: {thread_id}")
    
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Use memory checkpointer for state persistence
        pipeline = build_graph(checkpointer=MemorySaver())
        
        initial_input = create_initial_state(user_message)
        final_state = pipeline.invoke(initial_input, config=config)
        
        response_text = format_response_for_slack(final_state)
        
        # Reply to Slack
        if channel_id and slack_client:
            send_slack_message(channel_id, response_text, thread_ts)
            logger.info(f"✅ Background processing success for {thread_id}")
            
    except Exception as e:
        logger.error(f"❌ Background pipeline error: {e}")
        # Optionally send error to Slack
        if channel_id and slack_client:
            send_slack_message(channel_id, f"❌ Error processing request: {str(e)}", thread_ts)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    
    # Slack URL Verification
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data.get("challenge")})
    
    user_message = data.get('message')
    thread_id = data.get('thread_id')
    channel_id = data.get('channel')
    thread_ts = None
    
    # Handle Slack Events
    if not user_message and 'event' in data:
        event = data['event']
        # Check for retries to avoid duplicate processing (best effort)
        if request.headers.get('X-Slack-Retry-Num'):
            logger.info(f"Ignoring retry attempt: {request.headers.get('X-Slack-Retry-Num')}")
            return jsonify({"status": "ignored_retry"}), 200
            
        if 'bot_id' in event:
            return jsonify({"status": "ignored_bot"}), 200
            
        user_message = event.get('text')
        thread_ts = event.get('thread_ts', event.get('ts'))
        thread_id = thread_ts
        channel_id = event.get('channel')

    # Fallback to default channel from config if not provided in request (e.g. via direct API)
    if not channel_id:
        channel_id = Config.SLACK_CHANNEL_ID

    if not thread_id:
        thread_id = str(uuid.uuid4())
    
    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    logger.info(f"Received request: {user_message} (Thread: {thread_id})")

    # Start background processing
    thread = threading.Thread(
        target=process_pipeline_background,
        args=(user_message, thread_id, channel_id, thread_ts)
    )
    thread.start()
    
    # Return immediate success to Slack to prevent timeouts/retries
    return jsonify({
        "status": "processing", 
        "message": "Request received and processing started",
        "thread_id": thread_id
    }), 200

def run_server():
    """Run Flask Server"""
    print("\n" + "="*80)
    print("🚀 Starting API/Slack Server")
    print("="*80)
    init_slack_client()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

# ==========================================
# CLI Logic
# ==========================================

def print_results(state: OverallState):
    """Pretty print CLI results"""
    print("\n" + "="*80)
    print("📊 RESULTS")
    print("="*80)
    print(f"\n📝 Question: {state['question']}")
    
    if state.get("generated_query"):
        print(f"\n🔹 SQL Query: {state['generated_query']}")
    if state.get("corrected_query"):
        print(f"\n🔸 Corrected: {state['corrected_query']}")
        
    if state.get("execution_success"):
        print(f"\n✅ Execution: SUCCESS")
        res = state.get("execution_result", {})
        print(f"📊 Count: {res.get('count', 0)}")
        print(f"\n{res.get('formatted', '')}")
    else:
        print(f"\n❌ Failed: {state.get('error_message')}")
    print("\n" + "="*80)

def run_cli_interactive():
    print("\n" + "="*80)
    print("🤖 MySQL NL-to-SQL Pipeline - Interactive")
    print("="*80)
    
    pipeline = build_graph()
    
    while True:
        try:
            q = input("\n💬 Question (or 'quit'): ").strip()
            if q.lower() in ['quit', 'exit', 'q']: break
            if not q: continue
            
            final_state = pipeline.invoke(create_initial_state(q))
            print_results(final_state)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def run_cli_single(question: str):
    pipeline = build_graph()
    try:
        final_state = pipeline.invoke(create_initial_state(question))
        print_results(final_state)
    except Exception as e:
        print(f"❌ Error: {e}")

# ==========================================
# Main Entry Point
# ==========================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NL-to-SQL Pipeline")
    parser.add_argument("--server", action="store_true", help="Run as Flask/Slack server")
    parser.add_argument("--question", "-q", type=str, help="Run single query")
    
    args = parser.parse_args()
    
    try:
        Config.validate()
        
        if args.server:
            run_server()
        elif args.question:
            run_cli_single(args.question)
        else:
            run_cli_interactive()
            
    except Exception as e:
        print(f"❌ Startup Error: {e}")
