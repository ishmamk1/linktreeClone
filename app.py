from flask import Flask, render_template,request, redirect, session
import sqlite3
from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, current_user, LoginManager, login_user, login_required,logout_user
from db import db_user_init

app = Flask(__name__)
login_manager = LoginManager(app)
app.secret_key = 'hello'
db = 'tree.db'
app.static_folder = 'static'
login_manager.login_view = 'login'

def createDB():
    """
        Create the necessary database tables if they don't already exist.

        This function establishes a connection to the SQLite database and creates the required
        tables for the Linktree clone application. It creates two tables: 'users' and 'links'.

        The 'users' table stores user information such as user ID, username, email, and password.
        The 'links' table stores link information, including link ID, user ID (foreign key to 'users'
        table), link name, and link URL.

        If the tables already exist in the database, this function will not modify them.
    """
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            ''')

    cursor.execute('''
                CREATE TABLE IF NOT EXISTS links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT,
                    url TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
    conn.commit()
    conn.close()
createDB()

def authenticate_user(username, password):
    """
        Authenticate a user based on provided credentials.

        Args:
            username (str): The username.
            password (str): The password.

        Returns:
            dict or None: User information (ID and username) if authenticated, otherwise None.
    """
    conn = sqlite3.connect('tree.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id, username, password FROM users WHERE username = ?', (username,))
    user_data = cursor.fetchone()

    conn.close()

    if user_data and user_data[2] == password:
        return {'user_id': user_data[0], 'username': user_data[1]}
    else:
        return None

def create_user(username, email, password):
    """
        Create a new user in the database.

        Args:
            username (str): The desired username.
            email (str): The email address of the user.
            password (str): The password for the user.

        Returns:
            int: The ID of the newly created user.
    """
    try:
        with sqlite3.connect('tree.db') as conn:
    # conn = sqlite3.connect(db)
            cursor = conn.cursor()

            # cursor.execute('SELECT * FROM users WHERE email = (?) ', (email,))

            cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, password,))
            user_id = cursor.lastrowid

    # conn.commit()
    # conn.close()

        return user_id

    except sqlite3.IntegrityError:
        return None


class User(UserMixin):
    """
        User class representing a user with authentication attributes.

        Args:
            user_id (int): The unique identifier of the user.
            username (str): The username of the user.
            email (str): The email address of the user.
        """
    def __init__(self, user_id, username, email):
        self.id = user_id
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    """
        Load a user from the database based on the user ID.

        Args:
            user_id (int): The unique identifier of the user.

        Returns:
            User or None: A User instance if the user is found in the database, otherwise None.
    """
    conn = sqlite3.connect('tree.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id, username, email FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()

    conn.close()

    if user_data:
        return User(user_data[0], user_data[1], user_data[2])
    else:
        return None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/index')
@login_required
def index():
    """
        Render the user's index page with their associated links.

        If the user is authenticated, fetches the links associated with their user ID
        from the database and renders the 'index.html' template with the links.

        Returns Rendered template 'index.html' with the user's links.
    """
    if current_user.is_authenticated:
        user_id = current_user.id
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('SELECT * FROM links WHERE user_id = ?', (current_user.id,))
        links = c.fetchall()
        conn.close()
        return render_template('index.html', links=links)
    else:
        return redirect('/login')

@app.route('/add_link/', methods=['POST', 'GET'])
@login_required
def add_link():
    """
        Add a new link for the authenticated user.

        If the request method is POST and the user is authenticated, retrieves the
        user's ID and the link's name and URL from the form. Inserts the new link into
        the database associated with the user's ID. Redirects to the 'index' page if
        successful, otherwise redirects to the 'login' page.

        Returns: Redirect to the 'index' or 'login' page based on the outcome of the link addition.
    """
    if request.method == 'POST' and current_user.is_authenticated:
        user_id = current_user.id
        name = request.form['name']
        url = request.form['url']

        if user_id:
            conn = sqlite3.connect(db)
            c = conn.cursor()
            c.execute('INSERT INTO links (user_id, name, url) VALUES (?, ?, ?)', (user_id, name, url))
            conn.commit()
            conn.close()
            return redirect('/index')
        else:
            return redirect('/login')
    return render_template('add_link.html')

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    """
        Delete a link from the database.

        Deletes the link with the specified ID from the database. This action can only be
        performed via a POST request. After the deletion, redirects to the 'index' page.

        Args:
            id (int): The ID of the link to be deleted.

        Returns Redirect to the 'index' page after successful deletion.
    """
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('DELETE FROM links WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/index')

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    """
        Update a link in the database.

        If the request method is POST, updates the link's name and URL with the new values
        from the form. Redirects to the 'index' page after successful update. If the request
        method is GET, retrieves the link details based on the specified ID and renders the
        'update.html' template.

        Args:
            id (int): The ID of the link to be updated.

        Returns: Redirect to 'index' page after successful update (POST), or render 'update.html' template with link details (GET).
    """
    if request.method == 'POST':
        name = request.form['name']
        url = request.form['url']
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('UPDATE links set name = ?, url = ? WHERE id = ?', (name, url,id))
        conn.commit()
        conn.close()
        return redirect('/index')
    else:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('SELECT * FROM links where id = ?', (id,))
        link = c.fetchone()
        conn.close()
        return render_template('update.html', link=link)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
        Handle user login.

        Allows users to log in with valid credentials.
        POST: Logs in the user and redirects to index on success.
              Displays error message on invalid credentials.

        Returns:
            GET: Renders login page.
            POST: Redirects to index or displays error on login page.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = authenticate_user(username, password)

        if user:
            # print(session['user_id'])
            # session['user_id'] = user['user_id']
            # session['username'] = user['username']
            # return redirect('/index')
            user_instance = load_user(user['user_id'])
            if user_instance:
                login_user(user_instance)
                return redirect('/index')
            else:
                error_message = "User not found."
                return render_template('login.html', error_message=error_message)



        else:
            error_message = "Invalid username or password. Please try again."
            return render_template('login.html', error_message=error_message)

    return render_template('login.html')

@login_required
@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
        Handle user signup.

        Allows users to sign up with unique credentials.
        POST: Creates a new user account and redirects to index on success.
              Displays error message if user already exists.

        Returns:
            GET: Renders signup page.
            POST: Redirects to index or displays error on signup page.
        """
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        existing_user = authenticate_user(username, password)

        if existing_user:
            error_message = "User with this email already exists."
            return render_template('signup.html', error_message=error_message)

        user_id = create_user(username, email, password)
        session['user_id'] = user_id
        session['username'] = username

        return redirect('/index')

    return render_template('signup.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/tos')
def tos():
    return render_template('tos.html')

@app.route('/links/<username>')
def links(username):
    """
        Display user-specific links.

        Displays links associated with a given username.
        - If user is logged in and viewing their own links, shows all links.
        - If viewing someone else's links or not logged in, shows public links.

        Args:
            username (str): The username for which to display the links.

        Returns:
            str: "User not found" if username doesn't exist.
            HTML: Rendered links page with appropriate links.
    """
    conn = sqlite3.connect(db)
    c = conn.cursor()

    # Retrieve the user's ID based on the provided username
    c.execute('SELECT id FROM users WHERE username = ?', (username,))
    user_id = c.fetchone()

    if user_id:
        user_id = user_id[0]

        if current_user.is_authenticated and username == current_user.username:
            # User is viewing their own links
            c.execute('SELECT * FROM links WHERE user_id = ?', (user_id,))
        else:
            # User is viewing someone else's links (or not logged in)
            c.execute('SELECT * FROM links WHERE user_id = ?', (user_id,))

        links = c.fetchall()
        conn.close()
        return render_template('links.html', links=links, username=username)
    else:
        # Handle case where the user doesn't exist
        conn.close()
        return "User not found"




if __name__ == '__main__':
    createDB()
    app.run(debug=True)
