# Adding User Authentication to Bank Statement Converter

## Overview
This authentication system adds user login, registration, and session management to your Bank Statement Converter application.

## Files Created
1. **`auth.py`** - Core authentication module
2. **`templates/login.html`** - Login page
3. **`templates/register.html`** - Registration page  
4. **`auth_routes.py`** - Authentication routes to integrate into app.py

## Installation Steps

### Step 1: Upload Files to Server
Upload these files to your server at `/home/converter/web/c.konsulence.al/public_html/Bank_Specific_Converter/`:
- `auth.py`
- `templates/login.html`
- `templates/register.html`

### Step 2: Modify app.py

Add these imports at the top of your `app.py`:

```python
from auth import (
    authenticate_user, create_user, get_user, login_required, 
    admin_required, initialize_default_admin, update_user_stats, load_users
)
```

Add this line after `app = Flask(__name__)`:

```python
# Initialize default admin user
initialize_default_admin()
```

### Step 3: Add Authentication Routes

Add these routes to your `app.py` (copy from `auth_routes.py`):

```python
@app.route('/login', methods=['GET', 'POST'])
def login():
    # ... (copy from auth_routes.py)

@app.route('/register', methods=['GET', 'POST'])
def register():
    # ... (copy from auth_routes.py)

@app.route('/logout')
def logout():
    # ... (copy from auth_routes.py)

@app.route('/profile')
@login_required
def profile():
    # ... (copy from auth_routes.py)

@app.route('/admin')
@admin_required
def admin():
    # ... (copy from auth_routes.py)
```

### Step 4: Protect Existing Routes

Add `@login_required` decorator to routes you want to protect:

```python
@app.route('/')
@login_required  # Add this line
def index():
    # existing code

@app.route('/convert', methods=['POST'])
@login_required  # Add this line
def convert():
    # existing code
    # After successful conversion, add:
    update_user_stats(session['username'])
```

### Step 5: Update Your Index Template

Add a logout button and user info to your index page. In your index template, add:

```html
<div class="user-info">
    Welcome, {{ session.username }}! 
    <a href="{{ url_for('profile') }}">Profile</a> | 
    <a href="{{ url_for('logout') }}">Logout</a>
</div>
```

### Step 6: Deploy to Server

```bash
# On your local machine
git add .
git commit -m "Add user authentication system"
git push origin main

# On the server (as converter user)
ssh converter@c.konsulence.al
cd ~/web/c.konsulence.al/public_html
git pull origin main

# Restart the Flask app
pkill -f "python app.py"
cd Bank_Specific_Converter
source ../.venv/bin/activate
nohup python app.py > app.log 2>&1 &
```

## Default Admin Account

After deployment, a default admin account will be created:

- **Username:** `admin`
- **Password:** `admin123`

⚠️ **IMPORTANT:** Change this password immediately after first login!

## Features

### For All Users:
- ✅ User registration
- ✅ Secure login/logout
- ✅ Password hashing (SHA-256 with salt)
- ✅ User profile page
- ✅ Conversion count tracking
- ✅ Session management

### For Administrators:
- ✅ Admin panel
- ✅ View all users
- ✅ System statistics
- ✅ User management dashboard

## Security Features

1. **Password Hashing**: All passwords are hashed with SHA-256 and a random salt
2. **Session Management**: Secure Flask sessions
3. **Route Protection**: Decorators to require login/admin privileges
4. **Input Validation**: Username and password requirements

## Usage

### For Users:
1. Visit `https://c.konsulence.al`
2. Click "Register" to create an account
3. Login with your credentials
4. Use the converter as normal
5. View your profile and stats at `/profile`

### For Admins:
1. Login with admin credentials
2. Access admin panel at `/admin`
3. View user statistics and management

## File Storage

User data is stored in `users.json` in the same directory as `app.py`. This file contains:
- Usernames
- Hashed passwords
- Email addresses
- Admin flags
- Login timestamps
- Conversion counts

## Customization

### Change Password Requirements

Edit `auth_routes.py`:

```python
if len(password) < 8:  # Change from 6 to 8
    flash('Password must be at least 8 characters long.', 'danger')
```

### Add Email Verification

You can extend the system to send verification emails by:
1. Installing `flask-mail`
2. Adding email sending to `create_user()`
3. Creating email verification routes

### Add Password Reset

Create new routes for password reset functionality:
1. Request reset (enter email)
2. Send reset token
3. Reset password with token

## Troubleshooting

### "Users file not found"
The file will be created automatically on first use. Ensure the directory is writable.

### "Admin user not created"
Check the console output when starting the app. You should see:
```
✅ Default admin user created: admin / admin123
```

### Users can't login
1. Check `users.json` exists
2. Verify passwords are being hashed correctly
3. Check Flask secret key is set

### Session expires immediately
Ensure `app.secret_key` is set in your Flask app configuration.

## Next Steps

After basic authentication is working, you can add:
1. **Email verification** for new registrations
2. **Password reset** functionality
3. **Two-factor authentication** (2FA)
4. **Role-based permissions** (viewer, converter, admin)
5. **Activity logs** to track all conversions
6. **API keys** for programmatic access
7. **Rate limiting** to prevent abuse

## Support

For issues or questions about the authentication system, check:
- `auth.py` for authentication logic
- `auth_routes.py` for route implementations
- Flask session documentation: https://flask.palletsprojects.com/en/2.3.x/quickstart/#sessions
