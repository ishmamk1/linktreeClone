import sqlite3

DB_file = "tree.db"
db = None

def db_connect():
    global db
    db = sqlite3.connect(DB_file)
    return db.cursor()

def db_close():
    db.commit()
    db.close()

def db_user_init():
    c = db_connect()
    c.execute("CREATE TABLE IF NOT EXISTS users (username text, password text, name text)")
    db_close()

def create_new_user(username, password, name): #creates new user
    c = db_connect()
    c.execute('INSERT INTO users VALUES (?,?,?)',(username, password, name))
    c.execute("SELECT * from users")
    db_close()

def check_credentials(username, password): #checks if there exists username and password in db, returns True if there is
    c = db_connect()
    c.execute('SELECT username,password FROM users WHERE username=? AND password=?',(username, password))
    user = c.fetchone()
    db_close()
    if user:
        return True
    return False