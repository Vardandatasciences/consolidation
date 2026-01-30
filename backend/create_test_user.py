"""
Script to create test users in the database
Run this file to create test users with plain text passwords
"""

from database import Database

def create_test_users():
    """Create test users in the database"""
    
    users = [
        {
            'username': 'admin',
            'email': 'admin@vardaan.com',
            'password': 'admin123',
            'role': 'ADMIN',
            'ent_id': None
        },
        {
            'username': 'demo',
            'email': 'demo@vardaan.com',
            'password': 'demo123',
            'role': 'ANALYST',
            'ent_id': None
        },
        {
            'username': 'test',
            'email': 'test@vardaan.com',
            'password': 'test123',
            'role': 'VIEWER',
            'ent_id': None
        }
    ]
    
    print("=" * 50)
    print("Creating test users...")
    print("=" * 50)
    
    for user_data in users:
        try:
            # Check if user already exists
            check_query = "SELECT user_id FROM users WHERE username = %s OR email = %s"
            existing = Database.execute_query(
                check_query, 
                (user_data['username'], user_data['email']), 
                fetch_one=True
            )
            
            if existing:
                print(f"⚠️  User '{user_data['username']}' already exists, skipping...")
                continue
            
            # Store password as plain text (no hashing)
            # Insert user
            insert_query = """
                INSERT INTO users (username, email, password, role, ent_id, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, 1, NOW())
            """
            
            user_id = Database.execute_query(
                insert_query,
                (
                    user_data['username'],
                    user_data['email'],
                    user_data['password'],  # Store as plain text
                    user_data['role'],
                    user_data['ent_id']
                )
            )
            
            print(f"✅ Created user: {user_data['username']} (ID: {user_id})")
            print(f"   Email: {user_data['email']}")
            print(f"   Password: {user_data['password']}")
            print(f"   Role: {user_data['role']}")
            print()
            
        except Exception as e:
            print(f"❌ Error creating user '{user_data['username']}': {str(e)}")
            print()
    
    print("=" * 50)
    print("Test users creation completed!")
    print("=" * 50)

if __name__ == '__main__':
    create_test_users()

