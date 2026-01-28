"""
Embedding utilities for creating and searching embeddings
NOTE: Neo4j functionality has been disabled. This file is kept for generic embedding support if needed.
"""
from openai import OpenAI
from typing import List, Dict, Any, Optional
from config import Config
# from neo4j_connection import get_neo4j_connection  # DISABLED


class EmbeddingManager:
    """Manage embeddings"""
    
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.EMBEDDING_MODEL
        # self.neo4j = get_neo4j_connection() # DISABLED
    
    def create_embedding(self, text: str) -> List[float]:
        """
        Create embedding for given text
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector as list of floats
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ Error creating embedding: {e}")
            raise
    
    def create_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for multiple texts in a batch
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"❌ Error creating batch embeddings: {e}")
            raise
    
    def store_query_example(
        self, 
        question: str, 
        cypher_query: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        DISABLED: Store a query example with its embedding
        """
        print("⚠️  Vector storage is disabled (Neo4j removed)")
        return False
        # try:
        #     # Create combined text for embedding
        #     combined_text = f"Question: {question}\nQuery: {cypher_query}"
        #     embedding = self.create_embedding(combined_text)
        #     
        #     # Store in Neo4j
        #     query = """
        #     MERGE (q:QueryExample {question: $question})
        #     SET q.cypher_query = $cypher_query,
        #         q.embedding = $embedding,
        #         q.created_at = datetime(),
        #         q.metadata = $metadata
        #     RETURN q
        #     """
        #     
        #     parameters = {
        #         "question": question,
        #         "cypher_query": cypher_query,
        #         "embedding": embedding,
        #         "metadata": metadata or {}
        #     }
        #     
        #     result = self.neo4j.execute_write(query, parameters)
        #     print(f"✅ Stored query example: '{question[:50]}...'")
        #     return True
        #     
        # except Exception as e:
        #     print(f"❌ Error storing query example: {e}")
        #     return False
    
    def find_similar_queries(
        self, 
        question: str, 
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        DISABLED: Find similar query examples using vector similarity search
        """
        print("⚠️  Vector search is disabled (Neo4j removed)")
        return []
        # try:
        #     # Create embedding for the question
        #     embedding = self.create_embedding(question)
        #     
        #     # Vector similarity search
        #     query = f"""
        #     CALL db.index.vector.queryNodes(
        #         $index_name,
        #         $top_k,
        #         $embedding
        #     ) YIELD node, score
        #     RETURN 
        #         node.question as question,
        #         node.cypher_query as cypher_query,
        #         node.metadata as metadata,
        #         score
        #     ORDER BY score DESC
        #     """
        #     
        #     parameters = {
        #         "index_name": Config.VECTOR_INDEX_NAME,
        #         "top_k": top_k,
        #         "embedding": embedding
        #     }
        #     
        #     results = self.neo4j.execute_query(query, parameters)
        #     
        #     if results:
        #         print(f"✅ Found {len(results)} similar queries")
        #     else:
        #         print("ℹ️  No similar queries found")
        #     
        #     return results
        #     
        # except Exception as e:
        #     print(f"❌ Error finding similar queries: {e}")
        #     return []
    
    def get_all_query_examples(self) -> List[Dict[str, Any]]:
        """
        DISABLED: Retrieve all stored query examples
        """
        return []
    
    def delete_query_example(self, question: str) -> bool:
        """DISABLED"""
        return False
    
    def clear_all_examples(self) -> bool:
        """DISABLED"""
        return False


if __name__ == "__main__":
    # Test embedding utilities
    print("Testing Embedding Manager (Neo4j Disabled)...")
    
    try:
        Config.validate()
        em = EmbeddingManager()
        
        # Test embedding creation (should still work if generic)
        print("\n1. Testing embedding creation...")
        test_text = "Show all users in the database"
        embedding = em.create_embedding(test_text)
        print(f"✅ Created embedding with {len(embedding)} dimensions")
        
        # Test disabled methods
        print("\n2. Testing disabled storage...")
        em.store_query_example("test", "test", {})
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
