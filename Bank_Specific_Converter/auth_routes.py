"""
Authentication Routes for Bank Statement Converter
Add these routes to your main app.py
"""

from flask import render_template, request, redirect, url_for, flash, session
from auth import (
    authenticate_user, create_user, get_user, login_required, 
    admin_required, initialize_default_admin, update_user_stats, load_users
)

# Add this at the beginning of your app.py after app = Flask(__name__)
# Initialize default admin if no users exist
initialize_default_admin()

# =============================================================================
# AUTHENTICATION ROUTES - Add these to your app.py
# =============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        success, result = authenticate_user(username, password)
        
        if success:
            session['username'] = username
            session['is_admin'] = result.get('is_admin', False)
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash(result, 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email', '')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if len(username) < 3:
            flash('Username must be at least 3 characters long.', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        
        success, message = create_user(username, password, email)
        
        if success:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'danger')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logout"""
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}!', 'success')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    user = get_user(session['username'])
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Profile - Bank Statement Converter</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 { color: #667eea; margin-bottom: 30px; }
        .profile-info {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #ddd;
        }
        .info-row:last-child { border-bottom: none; }
        .label { font-weight: 600; color: #555; }
        .value { color: #333; }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-admin { background-color: #dc3545; color: white; }
        .badge-user { background-color: #28a745; color: white; }
        .btn-group {
            margin-top: 20px;
            display: flex;
            gap: 10px;
        }
        .btn {
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: 600;
            display: inline-block;
            transition: transform 0.2s;
        }
        .btn:hover { transform: translateY(-2px); }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>👤 User Profile</h1>
        
        <div class="profile-info">
            <div class="info-row">
                <span class="label">Username:</span>
                <span class="value">{{ user.username }}</span>
            </div>
            <div class="info-row">
                <span class="label">Email:</span>
                <span class="value">{{ user.email or 'Not provided' }}</span>
            </div>
            <div class="info-row">
                <span class="label">Account Type:</span>
                <span class="value">
                    {% if user.is_admin %}
                        <span class="badge badge-admin">Admin</span>
                    {% else %}
                        <span class="badge badge-user">User</span>
                    {% endif %}
                </span>
            </div>
            <div class="info-row">
                <span class="label">Member Since:</span>
                <span class="value">{{ user.created_at[:10] }}</span>
            </div>
            <div class="info-row">
                <span class="label">Last Login:</span>
                <span class="value">{{ user.last_login[:19] if user.last_login else 'Never' }}</span>
            </div>
            <div class="info-row">
                <span class="label">Total Conversions:</span>
                <span class="value">{{ user.conversions_count }}</span>
            </div>
        </div>
        
        <div class="btn-group">
            <a href="{{ url_for('index') }}" class="btn btn-primary">🏦 Back to Converter</a>
            {% if user.is_admin %}
                <a href="{{ url_for('admin') }}" class="btn btn-secondary">⚙️ Admin Panel</a>
            {% endif %}
            <a href="{{ url_for('logout') }}" class="btn btn-secondary">🚪 Logout</a>
        </div>
    </div>
</body>
</html>
    ''', user={'username': session['username'], **user})

@app.route('/admin')
@admin_required
def admin():
    """Admin panel"""
    users = load_users()
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel - Bank Statement Converter</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 { color: #667eea; margin-bottom: 30px; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #667eea;
            color: white;
            font-weight: 600;
        }
        tr:hover { background-color: #f8f9fa; }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-admin { background-color: #dc3545; color: white; }
        .badge-user { background-color: #28a745; color: white; }
        .btn {
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: 600;
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin-top: 20px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-number {
            font-size: 36px;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }
        .stat-label {
            font-size: 14px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚙️ Admin Panel</h1>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ users|length }}</div>
                <div class="stat-label">Total Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ admin_count }}</div>
                <div class="stat-label">Administrators</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ total_conversions }}</div>
                <div class="stat-label">Total Conversions</div>
            </div>
        </div>
        
        <h2>User Management</h2>
        <table>
            <thead>
                <tr>
                    <th>Username</th>
                    <th>Email</th>
                    <th>Type</th>
                    <th>Conversions</th>
                    <th>Last Login</th>
                    <th>Created</th>
                </tr>
            </thead>
            <tbody>
                {% for username, user in users.items() %}
                <tr>
                    <td>{{ username }}</td>
                    <td>{{ user.email or 'N/A' }}</td>
                    <td>
                        {% if user.is_admin %}
                            <span class="badge badge-admin">Admin</span>
                        {% else %}
                            <span class="badge badge-user">User</span>
                        {% endif %}
                    </td>
                    <td>{{ user.conversions_count }}</td>
                    <td>{{ user.last_login[:19] if user.last_login else 'Never' }}</td>
                    <td>{{ user.created_at[:10] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <a href="{{ url_for('index') }}" class="btn">🏦 Back to Converter</a>
    </div>
</body>
</html>
    ''', 
    users=users,
    admin_count=sum(1 for u in users.values() if u.get('is_admin')),
    total_conversions=sum(u.get('conversions_count', 0) for u in users.values())
    )

# =============================================================================
# MODIFY EXISTING ROUTES TO REQUIRE LOGIN
# =============================================================================

# Replace your existing @app.route('/') with this:
@app.route('/')
@login_required  # Add this decorator
def index():
    """Main page - now requires login"""
    # Your existing index() code here
    # Add username to the template context
    username = session.get('username', 'User')
    # ... rest of your existing index code
    pass

# Replace your existing convert route with this:
@app.route('/convert', methods=['POST'])
@login_required  # Add this decorator
def convert():
    """Convert file - now requires login and tracks stats"""
    # Your existing convert() code here
    # After successful conversion, update user stats:
    update_user_stats(session['username'])
    # ... rest of your existing convert code
    pass
