"""
Custom exception types for NL-to-SQL Pipeline
"""

class NLToSQLError(Exception):
    """Base exception for all NL-to-SQL errors"""
    pass

class DatabaseConnectionError(NLToSQLError):
    """Raised when database connection fails"""
    pass

class QueryExecutionError(NLToSQLError):
    """Raised when SQL query execution fails"""
    pass

class LLMGenerationError(NLToSQLError):
    """Raised when LLM fails to generate a response"""
    pass

class ValidationError(NLToSQLError):
    """Raised when a query fails validation"""
    pass

class ConfigurationError(NLToSQLError):
    """Raised when application configuration is invalid"""
    pass
