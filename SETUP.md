# Quick Setup Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies
```bash
pip install -r req.txt
```

### Step 2: Configure Environment Variables

Edit the `.env` file and add your credentials:

```env
# Required: Add your Neo4j password
NEO4J_PASSWORD=your_neo4j_password_here

# Required: Add your OpenAI API key
OPENAI_API_KEY=sk-your_openai_api_key_here
```

### Step 3: Verify Configuration
```bash
python config.py
```

You should see:
```
========================================
Configuration Summary
========================================
...
✅ Configuration is valid!
```

### Step 4: Test Neo4j Connection
```bash
python neo4j_connection.py
```

This will:
- ✅ Connect to Neo4j
- ✅ Run health check
- ✅ Extract schema
- ✅ Create vector index

### Step 5: Run the Application
```bash
python app.py
```

## 🎯 Try These Example Questions

Once the application is running, try:

1. **Simple Query**:
   ```
   Show all users
   ```

2. **With Filtering**:
   ```
   Find users who ordered products in the last 30 days
   ```

3. **Aggregation**:
   ```
   What is the average order value per customer?
   ```

4. **Top N**:
   ```
   Find the top 5 most popular products
   ```

## ⚠️ Troubleshooting

### "No driver has been set"
- **Issue**: Neo4j connection failed
- **Fix**: Check your Neo4j credentials in `.env`

### "Authentication failed"
- **Issue**: Wrong Neo4j password
- **Fix**: Update `NEO4J_PASSWORD` in `.env`

### "OpenAI API error"
- **Issue**: Invalid or missing API key
- **Fix**: Update `OPENAI_API_KEY` in `.env`

### "Vector index not found"
- **Issue**: Index not created
- **Fix**: Run `python neo4j_connection.py`

## 📖 Full Documentation

See [README.md](README.md) for complete documentation.

## 🧪 Testing Individual Components

Test each component independently:

```bash
# Connection & Schema
python neo4j_connection.py

# Embeddings
python embeddings_utils.py

# Schema Loader
python schema_loader.py

# Node 1: NL to Query
python node_nl_to_query.py

# Node 2: Validator
python node_query_validator.py

# Node 3: Corrector
python node_query_corrector.py

# Node 4: Executor
python node_query_executor.py
```

## 💡 Tips

1. **First Run**: The first query might take longer as it initializes everything
2. **Learning**: The system gets better over time as it stores successful queries
3. **Schema**: Make sure your Neo4j database has some data (nodes and relationships)
4. **Models**: Using `gpt-4` instead of `gpt-4o-mini` gives better results but costs more

## 🎉 You're Ready!

Your LangGraph NL-to-Query Pipeline is set up and ready to use!
