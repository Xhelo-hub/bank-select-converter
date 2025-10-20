import json
from auth import User

# Test loading users.json directly
try:
    with open('users.json', 'r') as f:
        data = json.load(f)
    print(f"JSON loaded successfully, {len(data)} entries")
    
    # Test creating User objects
    for i, user_data in enumerate(data):
        try:
            user = User.from_dict(user_data)
            print(f"User {i+1}: {user.email} - Success")
        except Exception as e:
            print(f"User {i+1}: Error creating User object - {e}")
            print(f"User data: {user_data}")
            
except Exception as e:
    print(f"Error loading JSON: {e}")