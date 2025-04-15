from db_connection import get_db, DatabaseConnectionManager

# Re-export get_db for backward compatibility
__all__ = ['get_db', 'get_db_connection']

# Get the global database manager instance
db_manager = DatabaseConnectionManager()

def get_db_connection():
    """
    Get a database connection. This function is provided for backward compatibility.
    It's recommended to use get_db() with a context manager instead.
    """
    conn, cursor = next(db_manager.get_connection().__enter__())
    return conn

if __name__ == "__main__":
    # Test the connection
    try:
        with get_db() as conn:
            print("Test: Connection to database works!")
    except Exception as e:
        print(f"Test: Database connection failed! Error: {str(e)}")
