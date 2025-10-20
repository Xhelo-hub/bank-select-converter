from flask_bcrypt import Bcrypt
import json

bcrypt = Bcrypt()
with open('users.json', 'r') as f:
    users = json.load(f)

user = users[0]  # kontakt@konsulence.al
print(f'Email: {user["email"]}')
print(f'Testing password admin123: {bcrypt.check_password_hash(user["password"], "admin123")}')
print(f'is_approved: {user.get("is_approved", False)}')
print(f'is_active: {user.get("is_active", True)}')