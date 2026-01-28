"""
Configuration management for LangGraph NL-to-Query Pipeline
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration"""
    
    # Neo4j Configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
    NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    # Slack Configuration
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "C0A34S2AVCJ") # Default test channel

    
    # Vector Index Configuration
    VECTOR_INDEX_NAME = os.getenv("VECTOR_INDEX_NAME", "query_examples_index")
    VECTOR_DIMENSIONS = int(os.getenv("VECTOR_DIMENSIONS", "1536"))
    
    # Query Generation Settings
    MAX_CORRECTION_ITERATIONS = int(os.getenv("MAX_CORRECTION_ITERATIONS", "3"))
    MAX_FEW_SHOT_EXAMPLES = int(os.getenv("MAX_FEW_SHOT_EXAMPLES", "5"))
    
    # MySQL Configuration (for SQL query execution)
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "")
    
    # Query Type: 'SQL' or 'CYPHER'
    QUERY_TYPE = os.getenv("QUERY_TYPE", "SQL").upper()
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present"""
        errors = []
        
        if not cls.NEO4J_PASSWORD:
            errors.append("NEO4J_PASSWORD is not set")
        
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is not set")
        
        if errors:
            raise ValueError(
                f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
            )
        
        return True
    
    @classmethod
    def display(cls):
        """Display current configuration (masking sensitive data)"""
        print("=" * 60)
        print("Configuration Summary")
        print("=" * 60)
        print(f"Query Type: {cls.QUERY_TYPE}")
        print(f"\n--- Neo4j Configuration (for embeddings) ---")
        print(f"Neo4j URI: {cls.NEO4J_URI}")
        print(f"Neo4j Database: {cls.NEO4J_DATABASE}")
        print(f"Neo4j Username: {cls.NEO4J_USERNAME}")
        print(f"Neo4j Password: {'*' * 8 if cls.NEO4J_PASSWORD else 'NOT SET'}")
        print(f"\n--- MySQL Configuration (for data queries) ---")
        print(f"MySQL Host: {cls.MYSQL_HOST}")
        print(f"MySQL Database: {cls.MYSQL_DATABASE}")
        print(f"MySQL User: {cls.MYSQL_USER}")
        print(f"MySQL Password: {'*' * 8 if cls.MYSQL_PASSWORD else 'NOT SET'}")
        print(f"\n--- OpenAI Configuration ---")
        print(f"OpenAI Model: {cls.OPENAI_MODEL}")
        print(f"Embedding Model: {cls.EMBEDDING_MODEL}")
        print(f"OpenAI API Key: {'*' * 20 if cls.OPENAI_API_KEY else 'NOT SET'}")
        print(f"\n--- Settings ---")
        print(f"Vector Index: {cls.VECTOR_INDEX_NAME}")
        print(f"Vector Dimensions: {cls.VECTOR_DIMENSIONS}")
        print(f"Max Corrections: {cls.MAX_CORRECTION_ITERATIONS}")
        print("=" * 60)


if __name__ == "__main__":
    # Test configuration
    try:
        Config.validate()
        Config.display()
        print("\n✅ Configuration is valid!")
    except ValueError as e:
        print(f"\n❌ {e}")
        print("\nPlease create a .env file based on .env.template")
