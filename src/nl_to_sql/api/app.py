"""
Main entry point for NL-to-SQL Pipeline API and CLI
"""
import os
import sys
import uuid
import argparse
import threading
from typing import Literal, Dict, Any, Optional

from flask import Flask, request, jsonify
from slack_sdk import WebClient
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from nl_to_sql.config import Config
from nl_to_sql.langgraph_schema import OverallState, create_initial_state
from nl_to_sql.pipeline.nodes.node_nl_to_query import nl_to_query_node
from nl_to_sql.pipeline.nodes.node_query_validator import validate_query_node
from nl_to_sql.pipeline.nodes.node_query_corrector import correct_query_node
from nl_to_sql.pipeline.nodes.node_query_executor import execute_query_node
from nl_to_sql.utils.logger import setup_logger

logger = setup_logger(__name__)

# ==========================================
# Core Pipeline Definition
# ==========================================

def route_after_validation(state: OverallState) -> Literal["execute", "correct", "end"]:
    """Routing logic after validation"""
    is_revalidation = state.get("corrected_query") is not None

    if is_revalidation:
        if state.get("final_validation_passed"):
            logger.info("🎯 Final validation passed")
            return "execute"
        else:
            iteration_count = state.get("iteration_count", 0)
            if iteration_count >= Config.MAX_CORRECTION_ITERATIONS:
                logger.warning(f"⚠️ Max iterations ({Config.MAX_CORRECTION_ITERATIONS}) reached")
                return "end"
            else:
                logger.info("🔄 Final validation failed, correcting again")
                return "correct"
    else:
        if state.get("validation_passed"):
            logger.info("✅ Initial validation passed")
            return "execute"
        else:
            logger.info("🔧 Initial validation failed, correcting query")
            return "correct"

def build_graph(checkpointer=None):
    """Build the LangGraph workflow"""
    workflow = StateGraph(OverallState)

    workflow.add_node("nl_to_sql", nl_to_query_node)
    workflow.add_node("validate_sql", validate_query_node)
    workflow.add_node("correct_sql", correct_query_node)
    workflow.add_node("execute_sql", execute_query_node)

    workflow.set_entry_point("nl_to_sql")
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

    return workflow.compile(checkpointer=checkpointer)

# ==========================================
# Flask / Slack Server Logic
# ==========================================

app = Flask(__name__)
slack_client = None

def init_slack_client():
    global slack_client
    if Config.SLACK_BOT_TOKEN:
        slack_client = WebClient(token=Config.SLACK_BOT_TOKEN)
        logger.info("✅ Slack client initialized")
    else:
        logger.warning("⚠️ SLACK_BOT_TOKEN not found - Slack messaging disabled")

def send_slack_message(channel, text, thread_ts=None):
    if not slack_client: return None
    try:
        return slack_client.chat_postMessage(channel=channel, text=text, thread_ts=thread_ts)
    except Exception as e:
        logger.error(f"Error sending Slack message: {e}")
        return None

def format_response_for_slack(state: Dict[str, Any]) -> str:
    if state.get("execution_success"):
        result_data = state.get("execution_result", {})
        sql_query = state.get("corrected_query") or state.get("generated_query")
        return (f"*Query Executed Successfully* ✅\n"
                f"Found {result_data.get('count', 0)} results.\n\n"
                f"```sql\n{sql_query}\n```\n\n"
                f"*Results:*\n{result_data.get('formatted', '')}")
    return f"❌ *Error Occurred:*\n{state.get('error_message', 'Process failed')}"

def process_pipeline_background(user_message, thread_id, channel_id, thread_ts):
    logger.info(f"🧵 Processing in background: {thread_id}")
    try:
        pipeline = build_graph(checkpointer=MemorySaver())
        final_state = pipeline.invoke(create_initial_state(user_message),
                                     config={"configurable": {"thread_id": thread_id}})
        if channel_id:
            send_slack_message(channel_id, format_response_for_slack(final_state), thread_ts)
    except Exception as e:
        logger.error(f"❌ Background pipeline error: {e}")
        if channel_id:
            send_slack_message(channel_id, f"❌ Error: {str(e)}", thread_ts)

@app.route('/health', methods=['GET'])
def health(): return jsonify({"status": "ok"}), 200

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data.get("challenge")})

    user_message = data.get('message')
    channel_id = data.get('channel') or Config.SLACK_CHANNEL_ID
    thread_ts = None

    if not user_message and 'event' in data:
        event = data['event']
        if request.headers.get('X-Slack-Retry-Num') or 'bot_id' in event:
            return jsonify({"status": "ignored"}), 200
        user_message = event.get('text')
        thread_ts = event.get('thread_ts', event.get('ts'))
        channel_id = event.get('channel')

    if not user_message: return jsonify({"error": "Message required"}), 400

    thread_id = thread_ts or str(uuid.uuid4())
    threading.Thread(target=process_pipeline_background,
                     args=(user_message, thread_id, channel_id, thread_ts)).start()

    return jsonify({"status": "processing", "thread_id": thread_id}), 200

# ==========================================
# CLI Logic
# ==========================================

def run_cli_interactive():
    print("\n" + "="*80 + "\n🤖 MySQL NL-to-SQL Pipeline - Interactive\n" + "="*80)
    pipeline = build_graph()
    while True:
        try:
            q = input("\n💬 Question (or 'quit'): ").strip()
            if q.lower() in ['quit', 'exit', 'q']: break
            if not q: continue
            final_state = pipeline.invoke(create_initial_state(q))
            print_results(final_state)
        except KeyboardInterrupt: break
        except Exception as e: print(f"❌ Error: {e}")

def print_results(state: OverallState):
    print("\n" + "="*80 + f"\n📊 RESULTS\nQuestion: {state['question']}")
    query = state.get("corrected_query") or state.get("generated_query")
    if query: print(f"🔹 SQL: {query}")
    if state.get("execution_success"):
        res = state.get("execution_result", {})
        print(f"✅ Success ({res.get('count', 0)} results)\n{res.get('formatted', '')}")
    else:
        print(f"❌ Failed: {state.get('error_message')}")
    print("="*80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", action="store_true")
    parser.add_argument("--question", "-q", type=str)
    args = parser.parse_args()

    if args.server:
        init_slack_client()
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    elif args.question:
        pipeline = build_graph()
        print_results(pipeline.invoke(create_initial_state(args.question)))
    else:
        run_cli_interactive()
