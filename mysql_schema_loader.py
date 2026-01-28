"""
MySQL schema extraction and formatting utilities
"""
from typing import Dict, Any
from mysql_connection import MySQLConnection


class MySQLSchemaLoader:
    """Extract and format MySQL schema for LLM context"""
    
    def __init__(self, mysql_conn: MySQLConnection):
        self.mysql = mysql_conn
        self._schema_cache = None
    
    def load_schema(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Load MySQL schema
        
        Args:
            use_cache: Use cached schema if available
        
        Returns:
            Schema dictionary
        """
        if use_cache and self._schema_cache:
            return self._schema_cache
        
        self._schema_cache = self.mysql.get_schema()
        return self._schema_cache
    
    def format_schema_for_llm(self) -> str:
        """
        Format schema as a human-readable string for LLM context
        
        Returns:
            Formatted schema description
        """
        schema = self.load_schema()
        
        lines = []
        lines.append("# MySQL Database Schema")
        lines.append("")
        lines.append(f"Database: {self.mysql.database}")
        lines.append("")
        
        # Tables and Columns
        if schema["tables"]:
            lines.append("## Tables:")
            for table_name in sorted(schema["tables"]):
                lines.append(f"\n### {table_name}")
                
                if table_name in schema["table_columns"]:
                    columns = schema["table_columns"][table_name]
                    lines.append("Columns:")
                    for col in columns:
                        col_name = col["COLUMN_NAME"]
                        data_type = col["DATA_TYPE"]
                        nullable = "NULL" if col["IS_NULLABLE"] == "YES" else "NOT NULL"
                        key_info = f" ({col['COLUMN_KEY']})" if col["COLUMN_KEY"] else ""
                        lines.append(f"  - {col_name}: {data_type} {nullable}{key_info}")
        
        return "\n".join(lines)
    
    def get_schema_summary(self) -> str:
        """
        Get a concise schema summary
        
        Returns:
            Brief schema summary
        """
        schema = self.load_schema()
        
        total_tables = len(schema['tables'])
        total_columns = sum(len(cols) for cols in schema['table_columns'].values())
        print(total_columns)
        
        return (
            f"Database '{self.mysql.database}' contains {total_tables} tables "
            f"with {total_columns} total columns."
        )


if __name__ == "__main__":
    # Test schema loader
    print("Testing MySQL Schema Loader...")
    
    mysql_config = {
        "host": "localhost",
        "user": "root",
        "password": "1234",
        "database": "test_harsh"
    }
    
    try:
        mysql_conn = MySQLConnection(**mysql_config)
        mysql_conn.connect()
        
        loader = MySQLSchemaLoader(mysql_conn)
        
        # Load schema
        schema = loader.load_schema()
        print(f"\n✅ Loaded schema: {loader.get_schema_summary()}")
        
        # Format for LLM
        print("\n" + "="*60)
        print(loader.format_schema_for_llm())
        print("="*60)
        
        mysql_conn.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
