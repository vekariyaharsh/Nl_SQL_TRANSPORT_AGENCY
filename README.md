# LangGraph NL-to-Query Pipeline for Neo4j

A robust Natural Language to Cypher query conversion system using LangGraph, with automatic validation, correction, and execution capabilities.

## 🌟 Features

- **4-Node LangGraph Workflow**:
  1. **NL to Query Generator**: Converts natural language to Cypher using LLM with few-shot examples
  2. **Query Validator**: Validates queries against Neo4j schema and best practices
  3. **Query Corrector**: Automatically fixes invalid queries based on validation feedback
  4. **Query Executor**: Executes validated queries and stores successful examples

- **Vector Search Integration**: 
  - Stores successful query examples as embeddings in Neo4j
  - Uses vector similarity search to find relevant past queries
  - Improves query generation with contextual examples

- **State Management**: 
  - Comprehensive state tracking throughout the workflow
  - Iteration counting for correction loops
  - Error tracking and handling

- **Conditional Routing**:
  - Automatic routing based on validation results
  - Maximum 3 correction iterations before giving up
  - Re-validation after each correction

## 📋 Prerequisites

- Python 3.8+
- Neo4j Database (running locally or remotely)
- OpenAI API Key

## 🚀 Installation

1. **Clone or navigate to the project directory**:
```bash
cd "d:\Other Ideas\NI_SQL"
```

2. **Create and activate virtual environment** (if not already done):
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
```

3. **Install dependencies**:
```bash
pip install -r req.txt
```

4. **Configure environment variables**:
   - Copy `.env.template` to `.env`
   - Edit `.env` and fill in your credentials:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password_here
NEO4J_DATABASE=neo4j

OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

5. **Initialize Neo4j vector index**:
```bash
python neo4j_connection.py
```

## 💻 Usage

### Interactive Mode (Recommended)

Run the application in interactive mode to ask multiple questions:

```bash
python app.py
```

or

```bash
python app.py --interactive
```

Example session:
```
💬 Your question: Show all users who ordered products in the last week

🚀 Starting LangGraph Pipeline
...
📊 RESULTS
Question: Show all users who ordered products in the last week
✅ Validation: PASSED
✅ Execution: SUCCESS
...
```

### Single Query Mode

Execute a single question from the command line:

```bash
python app.py --question "Find the top 5 most popular products"
```

or

```bash
python app.py -q "What is the average order value?"
```

## 🏗️ Architecture

### Workflow Diagram

```
┌─────────────────┐
│  User Question  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Node 1: NL to Query    │
│  - LLM generation       │
│  - Few-shot examples    │
│  - Vector search context│
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Node 2: Validator      │
│  - Syntax check         │
│  - Schema validation    │
│  - Best practices check │
└────────┬────────────────┘
         │
    ┌────┴────┐
    │ Valid?  │
    └────┬────┘
         │
    ┌────┴────────┐
    │             │
    ▼             ▼
   YES           NO
    │             │
    │        ┌────▼────────────────┐
    │        │ Node 3: Corrector   │
    │        │ - Fix based on      │
    │        │   feedback          │
    │        │ - Max 3 iterations  │
    │        └────┬────────────────┘
    │             │
    │             ▼
    │        (Re-validate)
    │             │
    │             ├─────────────┐
    │             │             │
    │        ┌────▼────┐   ┌────▼────┐
    │        │ Valid?  │   │ Max     │
    │        │   YES   │   │ Iters?  │
    │        └────┬────┘   └────┬────┘
    │             │             │
    │             │             ▼
    │             │          END (Failed)
    │             │
    └─────────────┘
         │
         ▼
┌─────────────────────────┐
│  Node 4: Executor       │
│  - Execute query        │
│  - Store as embedding   │
│  - Return results       │
└────────┬────────────────┘
         │
         ▼
    ┌─────────┐
    │   END   │
    └─────────┘
```

### File Structure

```
NI_SQL/
├── app.py                      # Main application (LangGraph workflow)
├── config.py                   # Configuration management
├── langgraph_schema.py         # State schema definition
│
├── Node implementations:
├── node_nl_to_query.py         # Node 1: NL to Query
├── node_query_validator.py     # Node 2: Validator
├── node_query_corrector.py     # Node 3: Corrector
├── node_query_executor.py      # Node 4: Executor
│
├── Utilities:
├── neo4j_connection.py         # Neo4j driver management
├── embeddings_utils.py         # OpenAI embeddings & vector search
├── schema_loader.py            # Schema extraction
├── few_shot_examples.py        # Query examples repository
│
├── Configuration:
├── .env                        # Your environment variables (create this)
├── .env.template               # Template for .env
└── req.txt                     # Python dependencies
```

## 🧪 Testing Individual Components

Each module can be tested independently:

```bash
# Test configuration
python config.py

# Test Neo4j connection
python neo4j_connection.py

# Test embeddings
python embeddings_utils.py

# Test schema loader
python schema_loader.py

# Test few-shot examples
python few_shot_examples.py

# Test individual nodes
python node_nl_to_query.py
python node_query_validator.py
python node_query_corrector.py
python node_query_executor.py
```

## 🔧 Configuration Options

Edit `.env` to customize:

- `MAX_CORRECTION_ITERATIONS`: Maximum times to attempt query correction (default: 3)
- `MAX_FEW_SHOT_EXAMPLES`: Number of few-shot examples to include in prompts (default: 5)
- `VECTOR_INDEX_NAME`: Name of Neo4j vector index (default: query_examples_index)
- `OPENAI_MODEL`: OpenAI model to use (default: gpt-4o-mini)
- `EMBEDDING_MODEL`: Embedding model (default: text-embedding-3-small)

## 📊 How Vector Search Works

1. **Storage**: When a query executes successfully, the NL question + Cypher query are stored as embeddings in Neo4j
2. **Retrieval**: For new questions, the system finds the top 3 most similar past queries
3. **Context**: Similar queries are used as additional context for the LLM to generate better queries

### Stored Information

Each `QueryExample` node contains:
- `question`: Natural language question
- `cypher_query`: Corresponding Cypher query
- `embedding`: Vector embedding (1536 dimensions)
- `created_at`: Timestamp
- `metadata`: Execution stats (result count, iterations, etc.)

## 🎯 Example Questions

Try these questions to test the system:

- "Show all users"
- "Find users who ordered products in the last 30 days"
- "What is the average order value per customer?"
- "List the top 5 most popular products"
- "Find products that have never been ordered"
- "Show users and their total spending"

## ⚠️ Troubleshooting

### Connection Issues

If you get connection errors:
1. Ensure Neo4j is running: `neo4j status`
2. Check your credentials in `.env`
3. Verify Neo4j URI is correct

### OpenAI API Errors

If you get OpenAI errors:
1. Check your API key in `.env`
2. Ensure you have sufficient credits
3. Verify internet connectivity

### Vector Index Issues

If vector search fails:
```bash
# Recreate the index
python -c "from neo4j_connection import Neo4jConnection; conn = Neo4jConnection(); conn.connect(); conn.create_vector_index(force_recreate=True)"
```

## 🛠️ Advanced Usage

### Adding Custom Few-Shot Examples

Edit `few_shot_examples.py` and add to the `EXAMPLES` list:

```python
{
    "question": "Your question here",
    "cypher": "MATCH ... RETURN ...",
    "explanation": "What this query does"
}
```

### Adjusting Correction Iterations

In `.env`:
```env
MAX_CORRECTION_ITERATIONS=5  # Increase from default 3
```

### Using Different LLM Models

In `.env`:
```env
OPENAI_MODEL=gpt-4  # Use GPT-4 instead of GPT-4o-mini
```

## 📝 License

This project is for educational and internal use.

## 🤝 Contributing

To add improvements:
1. Test individual components first
2. Update relevant node implementations
3. Add examples to `few_shot_examples.py`
4. Update this README

## 📧 Support

For issues or questions, check the troubleshooting section above or review the individual component test outputs.
