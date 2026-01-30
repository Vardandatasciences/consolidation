import mysql.connector
from mysql.connector import Error
from config import Config

class Database:
    """Database connection handler without pooling"""
    
    @classmethod
    def get_connection(cls):
        """Create a fresh connection per request."""
        try:
            return mysql.connector.connect(
                host=Config.DB_HOST,
                database=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                port=Config.DB_PORT,
                autocommit=False,
            )
        except Error as e:
            print(f"❌ Error creating database connection: {e}")
            raise e
    
    @classmethod
    def execute_query(cls, query, params=None, fetch_one=False, fetch_all=False):
        """Execute a query and return results"""
        connection = None
        cursor = None
        try:
            connection = cls.get_connection()
            # Buffered cursor avoids "Unread result found" when multiple statements
            # are executed on the same connection before all results are consumed.
            cursor = connection.cursor(dictionary=True, buffered=True)
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_one:
                result = cursor.fetchone()
                return result
            elif fetch_all:
                result = cursor.fetchall()
                return result
            else:
                connection.commit()
                return cursor.lastrowid
                
        except Error as e:
            if connection:
                connection.rollback()
            print(f"❌ Database error: {e}")
            raise e
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    @classmethod
    def test_connection(cls):
        """Test database connection"""
        try:
            connection = cls.get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            connection.close()
            print("✅ Database connection test successful")
            return True
        except Error as e:
            print(f"❌ Database connection test failed: {e}")
            return False

