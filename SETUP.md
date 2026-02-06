# Setup Guide: NL-to-SQL Logistics Pipeline

Follow these steps to set up the production-level NL-to-SQL pipeline.

## Prerequisites
- Python 3.10+
- MySQL Server
- OpenAI API Key

## 1. Environment Setup
Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # Or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## 2. Configuration
Copy the configuration template to `.env` and fill in your details:
```bash
cp .env.template .env
```
Ensure the following variables are set:
- `OPENAI_API_KEY`
- `MYSQL_HOST`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`

## 3. Database Preparation
Ensure your MySQL database contains the logistics data (e.g., `lr_dump` table). The system will automatically load the schema for context.

## 4. Running the Application
The application is structured as a Python package. Always include the `src` directory in your `PYTHONPATH`.

### Local Interactive Shell
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python -m nl_to_sql.api.app
```

### Running Tests
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
pytest tests/
```
