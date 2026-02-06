"""
Database connection management for MySQL
"""
import mysql.connector
from mysql.connector import pooling
import threading
from typing import List, Dict, Any, Optional

from nl_to_sql.config import Config
from nl_to_sql.utils.logger import setup_logger
from nl_to_sql.utils.exceptions import DatabaseConnectionError, QueryExecutionError

logger = setup_logger(__name__)

class DatabaseManager:
    """Manages MySQL connection pooling and query execution"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        try:
            self.pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="nl_to_sql_pool",
                pool_size=5,
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DATABASE
            )
            logger.info(f"✅ MySQL Connection Pool initialized: {Config.MYSQL_HOST}/{Config.MYSQL_DATABASE}")
            self._initialized = True
        except mysql.connector.Error as e:
            logger.error(f"❌ Failed to initialize MySQL Pool: {e}")
            raise DatabaseConnectionError(f"MySQL Pool Initialization failed: {e}")

    def get_connection(self):
        """Get a connection from the pool"""
        try:
            return self.pool.get_connection()
        except mysql.connector.Error as e:
            logger.error(f"❌ Failed to get connection from pool: {e}")
            raise DatabaseConnectionError(f"Failed to get MySQL connection: {e}")

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as a list of dictionaries"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)

            logger.debug(f"Executing query: {query}")
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            return results
        except mysql.connector.Error as e:
            logger.error(f"❌ Query execution failed: {e}")
            logger.error(f"Query: {query}")
            raise QueryExecutionError(f"MySQL Query failed: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_schema_info(self) -> List[Dict[str, Any]]:
        """Fetch table and column information for the database"""
        query = """
        SELECT
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_KEY
        FROM
            INFORMATION_SCHEMA.COLUMNS
        WHERE
            TABLE_SCHEMA = %s
        ORDER BY
            TABLE_NAME, ORDINAL_POSITION
        """
        return self.execute_query(query, (Config.MYSQL_DATABASE,))
