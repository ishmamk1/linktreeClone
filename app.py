from flask import Flask, render_template,request, redirect
import sqlite3
import datetime

app = Flask(__name__)
db = 'tree.db'


def createDB():
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS links
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                url TEXT)''')
    conn.commit()
    conn.close()

createDB()

@app.route('/')
def index():
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('SELECT * FROM links')
    links = c.fetchall()
    conn.close()
    return render_template('index.html', links=links)

@app.route('/add_link/', methods=['POST', 'GET'])
def add_link():
    if request.method == 'POST':
        name = request.form['name']
        url = request.form['url']
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('INSERT INTO links (name, url) VALUES (?, ?)', (name, url))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('add_link.html')

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('DELETE FROM links WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    if request.method == 'POST':
        name = request.form['name']
        url = request.form['url']
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('UPDATE links set name = ?, url = ? WHERE id = ?', (name, url,id))
        conn.commit()
        conn.close()
        return redirect('/')
    else:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('SELECT * FROM links where id = ?', (id,))
        link = c.fetchone()
        conn.close()
        return render_template('update.html', link=link)


if __name__ == '__main__':
    app.run(debug=True)