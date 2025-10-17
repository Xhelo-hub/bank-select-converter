#!/usr/bin/env python3
"""
Script to add authentication to existing app.py
This will backup the original and create an authenticated version
"""

import os
import shutil
from datetime import datetime

def integrate_auth():
    """Integrate authentication into existing app.py"""
    
    app_file = 'app.py'
    backup_file = f'app.py.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    print("🔐 Integrating Authentication into app.py")
    print("=" * 60)
    
    # Backup original
    print(f"📦 Creating backup: {backup_file}")
    shutil.copy(app_file, backup_file)
    
    # Read original file
    with open(app_file, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    # Find import section
    import_section_end = original_content.find('app = Flask(__name__)')
    
    # New imports to add
    new_imports = """from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from auth import User, UserManager
from auth_routes import create_auth_routes
"""
    
    # Add imports
    content = original_content[:import_section_end] + new_imports + "\n" + original_content[import_section_end:]
    
    # Find where to add login manager initialization (after app = Flask...)
    app_init_pos = content.find("app = Flask(__name__)") + len("app = Flask(__name__)")
    
    login_manager_init = """

# Initialize authentication
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access the converter.'
login_manager.login_message_category = 'info'

user_manager = UserManager()

@login_manager.user_loader
def load_user(user_id):
    return user_manager.get_user_by_id(user_id)

# Register authentication routes
auth_blueprint = create_auth_routes(user_manager)
app.register_blueprint(auth_blueprint, url_prefix='/auth')
"""
    
    content = content[:app_init_pos] + login_manager_init + content[app_init_pos:]
    
    # Add @login_required to protected routes
    routes_to_protect = [
        "def index():",
        "def upload_file():",
        "def check_status(job_id):",
        "def download_file(job_id):"
    ]
    
    for route in routes_to_protect:
        pos = content.find(route)
        if pos > 0:
            # Find the @app.route decorator before this function
            route_decorator_pos = content.rfind('@app.route', 0, pos)
            if route_decorator_pos > 0:
                # Insert @login_required before the function
                insert_pos = content.find('\n', route_decorator_pos) + 1
                # Check if @login_required is not already there
                check_section = content[insert_pos:insert_pos+100]
                if '@login_required' not in check_section:
                    content = content[:insert_pos] + "@login_required\n" + content[insert_pos:]
                    print(f"✅ Protected route: {route}")
    
    # Update the startup message
    startup_msg_pos = content.find('print("🏦 Bank-Specific Albanian Statement Converter")')
    if startup_msg_pos > 0:
        end_of_line = content.find('\n', startup_msg_pos)
        content = content[:end_of_line] + '\n    print("🔐 WITH USER AUTHENTICATION")' + content[end_of_line:]
    
    # Add auth endpoints to startup message
    startup_end = content.find('app.run(host=')
    if startup_end > 0:
        auth_info = '''    print("=" * 60)
    print("🔐 Authentication enabled:")
    print("   - Login: /auth/login")
    print("   - Register: /auth/register")
    print("   - Logout: /auth/logout")
'''
        content = content[:startup_end] + auth_info + "    " + content[startup_end:]
    
    # Write new file
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("=" * 60)
    print("✅ Authentication integrated successfully!")
    print(f"📄 Original backed up to: {backup_file}")
    print("")
    print("Next steps:")
    print("1. Install dependencies: pip install flask-login flask-bcrypt")
    print("2. Create users.json file: touch users.json && echo '[]' > users.json")
    print("3. Restart Flask app")
    print("4. Visit /auth/register to create first user")
    print("=" * 60)

if __name__ == '__main__':
    integrate_auth()
