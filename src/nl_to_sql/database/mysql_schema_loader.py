"""
MySQL schema extraction and formatting utilities
"""
from typing import Dict, Any, List
from nl_to_sql.database.database_manager import DatabaseManager
from nl_to_sql.utils.logger import setup_logger

logger = setup_logger(__name__)

class MySQLSchemaLoader:
    """Extract and format MySQL schema for LLM context"""

    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()
        self._schema_cache = None

    def load_schema(self, use_cache: bool = True) -> Dict[str, Any]:
        """Load MySQL schema and organize it by table"""
        if use_cache and self._schema_cache:
            return self._schema_cache

        try:
            raw_columns = self.db.get_schema_info()

            schema = {
                "tables": set(),
                "table_columns": {}
            }

            for col in raw_columns:
                table_name = col["TABLE_NAME"]
                schema["tables"].add(table_name)

                if table_name not in schema["table_columns"]:
                    schema["table_columns"][table_name] = []

                schema["table_columns"][table_name].append(col)

            self._schema_cache = schema
            return schema
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            return {"tables": [], "table_columns": {}}

    def format_schema_for_llm(self) -> str:
        """Format schema as a human-readable string for LLM context"""
        schema = self.load_schema()

        lines = []
        lines.append("# MySQL Database Schema")
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
