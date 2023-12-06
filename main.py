import base64
import calendar
import os
import sqlite3
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for, session

app = Flask(__name__)

users = {'username1': 'password1', 'username2': 'password2'}
app.secret_key = 'your_secret_key'


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)
    return conn


DATABASE_FILE = 'static/data/photo_db.db'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users.get(username) == password:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return 'Invalid username or password'
    return render_template('login.html')


@app.route('/')
def home():
    username = session.get('username')
    if username:
        return render_template('index.html', username=username)
    else:
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/sales', methods=['GET'])
def photosFunction():
    conn = create_connection(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            strftime('%m', date) as Month, 
            COUNT(*) as PhotoCount 
        FROM 
            photo 
        GROUP BY 
            strftime('%m', date)
        ORDER BY 
            Month ASC;
    """)
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    month_names = list(calendar.month_name)[1:]
    labels = month_names
    data = [0] * 12

    for row in results:
        month_index = int(row[0]) - 1
        data[month_index] = row[1]

    return render_template("line_graph_example.html", data=data, labels=labels)


@app.route('/photos')
def photos():
    month = request.args.get('month', '')
    month_names = list(calendar.month_name)[1:]
    months = [(i, month_names[i-1]) for i in range(1, 13)]

    conn = create_connection(DATABASE_FILE)
    cursor = conn.cursor()

    if month:
        query = "SELECT id, image_blob, date FROM photo WHERE strftime('%m', date) = ?"
        cursor.execute(query, (f'{int(month):02}',))
    else:
        query = "SELECT id, image_blob, date FROM photo"
        cursor.execute(query)

    images = [
        {
            "id": row[0],
            "data": base64.b64encode(row[1]).decode('utf-8'),
            "date": row[2]
        }
        for row in cursor.fetchall()
    ]

    cursor.close()
    conn.close()

    return render_template('photo.html', images=images, month=month, month_names=month_names)


@app.route('/photos/<int:month>')
def photos_by_month(month):
    conn = create_connection(DATABASE_FILE)
    cursor = conn.cursor()
    query = "SELECT id, image_blob, date FROM photo WHERE strftime('%m', date) = ?"
    cursor.execute(query, (f'{month:02}',))
    images = [
        {
            "id": row[0],
            "data": base64.b64encode(row[1]).decode('utf-8'),
            "date": row[2]
        }
        for row in cursor.fetchall()
    ]
    cursor.close()
    conn.close()
    return render_template('photo.html', images=images)


def insert_image(image_path):
    conn = create_connection(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS photo (
            id INTEGER PRIMARY KEY,
            image_blob BLOB,
            date DATETIME
        );
    ''')
    with open(image_path, 'rb') as file:
        image_blob = file.read()
    current_time = datetime.now()
    cursor.execute("INSERT INTO photo (image_blob, date) VALUES (?, ?)", (image_blob, current_time))
    conn.commit()
    cursor.close()
    conn.close()


if __name__ == '__main__':
    insert_image('static/images/image3.png')
    app.run(debug=True)
