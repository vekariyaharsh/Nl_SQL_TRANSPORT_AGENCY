"""
MySQL/SQL database connection management and utilities
"""
import mysql.connector
from mysql.connector import Error
from typing import Optional, List, Dict, Any
from config import Config


class MySQLConnection:
    """MySQL database connection manager"""
    
    def __init__(
        self,
        host: str = "localhost",
        user: str = "root",
        password: str = "1234",
        database: str = "test_harsh"
    ):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
    
    def connect(self):
        """Establish connection to MySQL"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4'
            )
            
            if self.connection.is_connected():
                print(f"✅ Connected to MySQL database '{self.database}'")
                return True
            
        except Error as e:
            print(f"❌ MySQL connection error: {e}")
            return False
    
    def close(self):
        """Close the MySQL connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("🔒 MySQL connection closed")
    
    def execute_query(
        self, 
        query: str, 
        parameters: Optional[tuple] = None,
        fetch_all: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results
        
        Args:
            query: SQL query string
            parameters: Optional query parameters
            fetch_all: If True, fetch all results; if False, fetch one
        
        Returns:
            List of result records as dictionaries
        """
        if not self.connection or not self.connection.is_connected():
            raise RuntimeError("Not connected to MySQL. Call connect() first.")
        
        results = []
        cursor = None
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, parameters or ())
            
            if fetch_all:
                results = cursor.fetchall()
            else:
                result = cursor.fetchone()
                results = [result] if result else []
            
            return results
            
        except Error as e:
            print(f"❌ Query execution error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def execute_write(
        self, 
        query: str, 
        parameters: Optional[tuple] = None
    ) -> int:
        """
        Execute a write query (INSERT, UPDATE, DELETE)
        
        Args:
            query: SQL query string
            parameters: Optional query parameters
        
        Returns:
            Number of affected rows
        """
        if not self.connection or not self.connection.is_connected():
            raise RuntimeError("Not connected to MySQL. Call connect() first.")
        
        cursor = None
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, parameters or ())
            self.connection.commit()
            
            return cursor.rowcount
            
        except Error as e:
            self.connection.rollback()
            print(f"❌ Write query error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def health_check(self) -> bool:
        """Check if MySQL connection is healthy"""
        try:
            result = self.execute_query("SELECT 1 as health")
            return len(result) > 0 and result[0].get("health") == 1
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Extract MySQL schema information
        
        Returns:
            Dictionary containing table names and their columns
        """
        schema = {
            "tables": [],
            "table_columns": {}
        }
        
        try:
            # Get table names
            tables_query = """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = %s
            """
            tables = self.execute_query(tables_query, (self.database,))
            schema["tables"] = [table["TABLE_NAME"] for table in tables]
            
            # Get columns for each table
            for table_name in schema["tables"]:
                columns_query = """
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    COLUMN_KEY
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
                """
                columns = self.execute_query(columns_query, (self.database, table_name))
                schema["table_columns"][table_name] = columns
            
            return schema
            
        except Exception as e:
            print(f"❌ Error extracting schema: {e}")
            return schema
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Singleton instance
_mysql_connection = None


def get_mysql_connection(
    host: str = "localhost",
    user: str = "root",
    password: str = "",
    database: str = ""
) -> MySQLConnection:
    """Get or create MySQL connection singleton"""
    global _mysql_connection
    
    if _mysql_connection is None:
        _mysql_connection = MySQLConnection(host, user, password, database)
        _mysql_connection.connect()
    
    return _mysql_connection


if __name__ == "__main__":
    # Test MySQL connection
    print("Testing MySQL connection...")
    
    # You can configure these via environment variables or directly
    mysql_config = {
        "host": "localhost",
        "user": "root",
        "password": "1234",  # Change this
        "database": "test_harsh"  # Change this
    }
    
    try:
        with MySQLConnection(**mysql_config) as conn:
            # Health check
            if conn.health_check():
                print("✅ Health check passed")
            
            # Get schema
            schema = conn.get_schema()
            print(f"\n📊 Schema Information:")
            print(f"  Tables: {schema['tables']}")
            
            for table_name, columns in schema['table_columns'].items():
                print(f"\n  Table: {table_name}")
                print(f"    Columns: {len(columns)}")
                for col in columns[:5]:  # Show first 5 columns
                    print(f"      - {col['COLUMN_NAME']} ({col['DATA_TYPE']})")
                if len(columns) > 5:
                    print(f"      ... and {len(columns) - 5} more columns")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
