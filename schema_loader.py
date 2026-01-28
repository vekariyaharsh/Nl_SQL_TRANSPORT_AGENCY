"""
Neo4j schema extraction and formatting utilities
"""
from typing import Dict, Any
from neo4j_connection import get_neo4j_connection
from mysql_connection import get_mysql_connection


class SchemaLoader:
    """Extract and format Neo4j schema for LLM context"""
    
    def __init__(self):
        self.neo4j = get_mysql_connection()
        self._schema_cache = None
    
    def load_schema(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Load Neo4j schema
        
        Args:
            use_cache: Use cached schema if available
        
        Returns:
            Schema dictionary
        """
        if use_cache and self._schema_cache:
            return self._schema_cache
        
        self._schema_cache = self.neo4j.get_schema()
        return self._schema_cache
    
    def format_schema_for_llm(self) -> str:
        """
        Format schema as a human-readable string for LLM context
        
        Returns:
            Formatted schema description
        """
        schema = self.load_schema()
        
        lines = []
        lines.append("# Neo4j Database Schema")
        lines.append("")
        
        # Node Labels
        if schema["node_labels"]:
            lines.append("## Node Labels:")
            for label in sorted(schema["node_labels"]):
                lines.append(f"- {label}")
                if label in schema["node_properties"]:
                    props = schema["node_properties"][label]
                    if props:
                        lines.append(f"  Properties: {', '.join(props)}")
            lines.append("")
        
        # Relationship Types
        if schema["relationship_types"]:
            lines.append("## Relationship Types:")
            for rel_type in sorted(schema["relationship_types"]):
                lines.append(f"- {rel_type}")
                if rel_type in schema["relationship_properties"]:
                    props = schema["relationship_properties"][rel_type]
                    if props:
                        lines.append(f"  Properties: {', '.join(props)}")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_schema_summary(self) -> str:
        """
        Get a concise schema summary
        
        Returns:
            Brief schema summary
        """
        schema = self.load_schema()
        
        return (
            f"Database contains {len(schema['node_labels'])} node types "
            f"and {len(schema['relationship_types'])} relationship types."
        )
    
    def get_node_samples(self, label: str, limit: int = 3) -> list:
        """
        Get sample nodes of a specific label
        
        Args:
            label: Node label
            limit: Number of samples
        
        Returns:
            List of sample nodes
        """
        query = f"""
        MATCH (n:{label})
        RETURN n
        LIMIT {limit}
        """
        
        try:
            results = self.neo4j.execute_query(query)
            return [record["n"] for record in results]
        except Exception as e:
            print(f"❌ Error getting node samples: {e}")
            return []


if __name__ == "__main__":
    # Test schema loader
    print("Testing Schema Loader...")
    
    try:
        loader = SchemaLoader()
        
        # Load schema
        schema = loader.load_schema()
        print(f"\n✅ Loaded schema: {loader.get_schema_summary()}")
        
        # Format for LLM
        print("\n" + "="*60)
        print(loader.format_schema_for_llm())
        print("="*60)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
