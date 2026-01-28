"""
Neo4j connection management and utilities
"""
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
from typing import Optional, List, Dict, Any
from config import Config


class Neo4jConnection:
    """Neo4j database connection manager"""
    
    def __init__(self):
        self.driver = None
        self.database = Config.NEO4J_DATABASE
    
    def connect(self):
        """Establish connection to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                Config.NEO4J_URI,
                auth=(Config.NEO4J_USERNAME, Config.NEO4J_PASSWORD),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=120
            )
            
            # Verify connectivity
            self.driver.verify_connectivity()
            print(f"✅ Connected to Neo4j at {Config.NEO4J_URI}")
            return True
            
        except AuthError as e:
            print(f"❌ Authentication failed: {e}")
            return False
        except ServiceUnavailable as e:
            print(f"❌ Neo4j service unavailable: {e}")
            return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def close(self):
        """Close the Neo4j connection"""
        if self.driver:
            self.driver.close()
            print("🔒 Neo4j connection closed")
    
    def execute_query(
        self, 
        query: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results
        
        Args:
            query: Cypher query string
            parameters: Optional query parameters
        
        Returns:
            List of result records as dictionaries
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")
        
        results = []
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, parameters or {})
            results = [dict(record) for record in result]
        
        return results
    
    def execute_write(
        self, 
        query: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a write transaction
        
        Args:
            query: Cypher query string
            parameters: Optional query parameters
        
        Returns:
            Summary of the transaction
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, parameters or {})
            summary = result.consume()
            
            return {
                "nodes_created": summary.counters.nodes_created,
                "relationships_created": summary.counters.relationships_created,
                "properties_set": summary.counters.properties_set,
                "labels_added": summary.counters.labels_added
            }
    
    def health_check(self) -> bool:
        """Check if Neo4j connection is healthy"""
        try:
            result = self.execute_query("RETURN 1 as health")
            return len(result) > 0 and result[0].get("health") == 1
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    def create_vector_index(self, force_recreate: bool = False):
        """
        Create vector index for query examples
        
        Args:
            force_recreate: If True, drop and recreate the index
        """
        index_name = Config.VECTOR_INDEX_NAME
        dimensions = Config.VECTOR_DIMENSIONS
        
        try:
            # Check if index exists
            check_query = """
            SHOW INDEXES
            YIELD name, type
            WHERE name = $index_name AND type = 'VECTOR'
            RETURN name
            """
            existing = self.execute_query(check_query, {"index_name": index_name})
            
            if existing:
                if force_recreate:
                    print(f"🗑️  Dropping existing index '{index_name}'...")
                    self.execute_query(f"DROP INDEX {index_name}")
                else:
                    print(f"✅ Vector index '{index_name}' already exists")
                    return
            
            # Create vector index
            create_index_query = f"""
            CREATE VECTOR INDEX {index_name} IF NOT EXISTS
            FOR (q:QueryExample)
            ON q.embedding
            OPTIONS {{
                indexConfig: {{
                    `vector.dimensions`: {dimensions},
                    `vector.similarity_function`: 'cosine'
                }}
            }}
            """
            
            self.execute_query(create_index_query)
            print(f"✅ Created vector index '{index_name}' with {dimensions} dimensions")
            
        except Exception as e:
            print(f"❌ Error creating vector index: {e}")
            raise
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Extract Neo4j schema information
        
        Returns:
            Dictionary containing node labels, relationship types, and properties
        """
        schema = {
            "node_labels": [],
            "relationship_types": [],
            "node_properties": {},
            "relationship_properties": {}
        }
        
        try:
            # Get node labels
            labels_query = "CALL db.labels() YIELD label RETURN label"
            labels = self.execute_query(labels_query)
            schema["node_labels"] = [record["label"] for record in labels]
            
            # Get relationship types
            rel_types_query = "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"
            rel_types = self.execute_query(rel_types_query)
            schema["relationship_types"] = [record["relationshipType"] for record in rel_types]
            
            # Get node properties
            for label in schema["node_labels"]:
                props_query = f"""
                MATCH (n:{label})
                WITH n LIMIT 1
                RETURN keys(n) as properties
                """
                props = self.execute_query(props_query)
                if props and props[0]["properties"]:
                    schema["node_properties"][label] = props[0]["properties"]
            
            # Get relationship properties
            for rel_type in schema["relationship_types"]:
                props_query = f"""
                MATCH ()-[r:{rel_type}]->()
                WITH r LIMIT 1
                RETURN keys(r) as properties
                """
                props = self.execute_query(props_query)
                if props and props[0]["properties"]:
                    schema["relationship_properties"][rel_type] = props[0]["properties"]
            
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
_neo4j_connection = None


def get_neo4j_connection() -> Neo4jConnection:
    """Get or create Neo4j connection singleton"""
    global _neo4j_connection
    
    if _neo4j_connection is None:
        _neo4j_connection = Neo4jConnection()
        _neo4j_connection.connect()
    
    return _neo4j_connection


if __name__ == "__main__":
    # Test Neo4j connection
    print("Testing Neo4j connection...")
    
    try:
        Config.validate()
        
        with Neo4jConnection() as conn:
            # Health check
            if conn.health_check():
                print("✅ Health check passed")
            
            # Get schema
            schema = conn.get_schema()
            print(f"\n📊 Schema Information:")
            print(f"  Node Labels: {schema['node_labels']}")
            print(f"  Relationship Types: {schema['relationship_types']}")
            
            # Create vector index
            conn.create_vector_index()
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
