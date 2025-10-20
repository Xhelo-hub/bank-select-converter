from auth import UserManager

user_manager = UserManager()
users = user_manager._load_users()
print(f"Number of users loaded: {len(users)}")
for user in users:
    print(f"User: {user.email}, ID: {user.id}")

test_user = user_manager.get_user_by_email("kontakt@konsulence.al")
print(f"Test user found: {test_user is not None}")
if test_user:
    print(f"Test user email: {test_user.email}")
    print(f"Test user active: {hasattr(test_user, 'is_active') and test_user.is_active}")