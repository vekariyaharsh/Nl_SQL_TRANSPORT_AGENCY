"""
Slack Integration for MySQL NL-to-SQL Pipeline
"""
import os
import uuid
import logging
from typing import Dict, Any, Literal
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from config import Config
from langgraph_schema import OverallState, create_initial_state

# Import the refactored nodes
from node_nl_to_query import nl_to_query_node
from node_query_validator import validate_query_node
from node_query_corrector import correct_query_node
from node_query_executor import execute_query_node

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config Validation
try:
    Config.validate()
except Exception as e:
    logger.warning(f"Config validation warning: {e}")

app = Flask(__name__)

# Initialize Slack Client
SLACK_BOT_TOKEN = Config.SLACK_BOT_TOKEN
slack_client = WebClient(token=SLACK_BOT_TOKEN) if SLACK_BOT_TOKEN else None

# Check pointer for state persistence in thread
memory = MemorySaver()

def route_after_validation(state: OverallState) -> Literal["execute", "correct", "end"]:
    """Routing logic after validation"""
    is_revalidation = state.get("corrected_query") is not None
    
    if is_revalidation:
        if state.get("final_validation_passed"):
            return "execute"
        else:
            iteration_count = state.get("iteration_count", 0)
            if iteration_count >= Config.MAX_CORRECTION_ITERATIONS:
                return "end"
            else:
                return "correct"
    else:
        if state.get("validation_passed"):
            return "execute"
        else:
            return "correct"

def build_graph():
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
    
    return workflow.compile(checkpointer=memory)

# Compile the graph
sql_pipeline_graph = build_graph()

def send_slack_message(channel, text, thread_ts=None):
    """Send message to Slack channel"""
    if not slack_client:
        logger.warning("Slack client not initialized - SLACK_BOT_TOKEN missing")
        return None
        
    try:
        logger.info(f"Sending message to channel: {channel}, thread: {thread_ts}")
        response = slack_client.chat_postMessage(
            channel=channel,
            text=text,
            thread_ts=thread_ts
        )
        logger.info(f"Message sent successfully: {response['ts']}")
        return response
    except SlackApiError as e:
        logger.error(f"Slack API error: {e.response['error']}")
        return None
    except Exception as e:
        logger.error(f"Error sending Slack message: {str(e)}")
        return None

def format_response_for_slack(state: Dict[str, Any]) -> str:
    """Format the pipeline result for Slack"""
    
    if state.get("execution_success"):
        result_data = state.get("execution_result", {})
        count = result_data.get("count", 0)
        formatted_rows = result_data.get("formatted", "")
        
        # Format the SQL query
        sql_query = state.get("corrected_query") or state.get("generated_query")
        
        response = f"*Query Executed Successfully* ✅\n"
        response += f"Found {count} results.\n\n"
        response += f"```sql\n{sql_query}\n```\n\n"
        response += f"*Results:*\n{formatted_rows}"
        return response
        
    elif state.get("error_message"):
        return f"❌ *Error Occurred:*\n{state['error_message']}"
    
    elif state.get("validation_passed") is False and state.get("final_validation_passed") is False:
         return f"❌ *Validation Failed:*\nQuestion could not be translated to valid SQL.\nReason: {state.get('validation_result')}"
         
    return "⚠️ Unknown state or process incomplete."

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    
    # Handle Slack URL Verification
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data.get("challenge")})
    
    user_message = data.get('message')
    thread_id = data.get('thread_id')
    channel_id = data.get('channel')
    thread_ts = None
    
    # Check for Slack Event structure
    if not user_message and 'event' in data:
        event = data['event']
        # Filter out bot messages to avoid loops
        if 'bot_id' in event:
            logger.info("Ignoring bot message")
            return jsonify({"status": "ignored_bot"}), 200
            
        user_message = event.get('text')
        # Use thread_ts if it exists (reply), otherwise use ts (new thread)
        thread_ts = event.get('thread_ts', event.get('ts'))
        # For LangGraph checkpointer, we use the Slack thread_ts as the thread_id
        # ensuring state persists within that Slack thread.
        thread_id = thread_ts 
        channel_id = event.get('channel')

    # Generate a new ID if still missing (for direct API calls)
    if not thread_id:
        thread_id = str(uuid.uuid4())
    
    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    logger.info(f"Processing message: {user_message}, thread: {thread_id}, channel: {channel_id}")

    # LangGraph config
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Create initial state
        initial_input = create_initial_state(user_message)
        
        # Invoke the agent
        # Note: We pass the full state dict for the first step
        final_state = sql_pipeline_graph.invoke(initial_input, config=config)
        
        # Format response
        response_text = format_response_for_slack(final_state)
        logger.info(f"Pipeline finished. Success: {final_state.get('execution_success')}")
        
        # Send response back to Slack ONLY if we have a channel
        if channel_id and slack_client:
            slack_response = send_slack_message(
                channel=channel_id,
                text=response_text,
                thread_ts=thread_ts
            )
            
            if slack_response:
                return jsonify({
                    "status": "success",
                    "sent_to_slack": True,
                    "thread_id": thread_id
                }), 200
        
        # Return JSON response with text
        return jsonify({
            "status": "success",
            "response": response_text,
            "thread_id": thread_id,
            "raw_state": {k: v for k, v in final_state.items() if k != "execution_result"} # Exclude large result data in JSON
        })
        
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        logger.error(error_msg)
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "status": "error",
            "error": error_msg
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
