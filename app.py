from flask import Flask, request, render_template, redirect, url_for
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

def get_db_connection():
    try:
        conn = mysql.connector.connect(user='root', password='example', host='mysql', database='lagerverwaltung')
        return conn
    except Error as e:
        print(f"Error: {e}")
        return None

def fetch_boxes(cursor):
    cursor.execute("""
        SELECT boxes.projektnummer, boxes.kunde, storage_locations.reihe, storage_locations.fach, storage_locations.id
        FROM boxes
        JOIN storage_locations ON boxes.lagerplatz_id = storage_locations.id
    """)
    return cursor.fetchall()

def fetch_storage_locations(cursor):
    cursor.execute("SELECT id, reihe, fach FROM storage_locations")
    return cursor.fetchall()

@app.route('/')
def index():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        boxes = fetch_boxes(cursor)
        storage_locations = fetch_storage_locations(cursor)
        cursor.close()
        conn.close()
        return render_template('index.html', boxes=boxes, storage_locations=storage_locations, message=None, highlight=None)
    else:
        return "Database connection failed."

@app.route('/find', methods=['POST'])
def find_box():
    projektnummer = request.form['projektnummer']
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT lagerplatz_id FROM boxes WHERE projektnummer = %s", (projektnummer,))
        location = cursor.fetchone()
        cursor.close()
        conn.close()
        if location:
            return redirect(url_for('index', highlight=location[0]))
        else:
            return redirect(url_for('index', message="Box not found."))
    else:
        return "Database connection failed."

@app.route('/add', methods=['POST'])
def add_box():
    projektnummer = request.form['projektnummer']
    kunde = request.form['kunde']
    lagerplatz_id = request.form['lagerplatz_id']
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO boxes (projektnummer, kunde, lagerplatz_id)
            VALUES (%s, %s, %s)
        """, (projektnummer, kunde, lagerplatz_id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('index'))
    else:
        return "Database connection failed."

@app.route('/edit', methods=['POST'])
def edit_box():
    projektnummer = request.form['projektnummer']
    kunde = request.form['kunde']
    lagerplatz_id = request.form['lagerplatz_id']
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE boxes
            SET kunde = %s, lagerplatz_id = %s
            WHERE projektnummer = %s
        """, (kunde, lagerplatz_id, projektnummer))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('index'))
    else:
        return "Database connection failed."

@app.route('/delete', methods=['POST'])
def delete_box():
    projektnummer = request.form['projektnummer']
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM boxes WHERE projektnummer = %s", (projektnummer,))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('index'))
    else:
        return "Database connection failed."

@app.route('/manage')
def manage_boxes():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        boxes = fetch_boxes(cursor)
        storage_locations = fetch_storage_locations(cursor)
        cursor.close()
        conn.close()
        return render_template('manage.html', boxes=boxes, storage_locations=storage_locations, message=None, highlight=None)
    else:
        return "Database connection failed."

@app.route('/find_manage', methods=['POST'])
def find_box_manage():
    projektnummer = request.form['projektnummer']
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT lagerplatz_id FROM boxes WHERE projektnummer = %s", (projektnummer,))
        location = cursor.fetchone()
        boxes = fetch_boxes(cursor)
        storage_locations = fetch_storage_locations(cursor)
        highlight = None
        message = None
        if location:
            cursor.execute("SELECT fach, reihe FROM storage_locations WHERE id = %s", (location[0],))
            place = cursor.fetchone()
            highlight = (place[1], place[0])
            message = f"Kiste mit Projektnummer {projektnummer} befindet sich an Fach {place[0]}, Reihe {place[1]}"
        else:
            message = "Kiste nicht gefunden."
        cursor.close()
        conn.close()
        return render_template('manage.html', message=message, highlight=highlight, boxes=boxes, storage_locations=storage_locations)
    else:
        return "Database connection failed."

@app.route('/print_label/<projektnummer>/<kunde>/<reihe>/<fach>/<boxnummer>')
def print_label(projektnummer, kunde, reihe, fach, boxnummer):
    return render_template('print_label.html', projektnummer=projektnummer, kunde=kunde, reihe=reihe, fach=fach, boxnummer=boxnummer)

@app.route('/delete_box/<projektnummer>', methods=['POST'])
def delete_box(projektnummer):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT lagerplatz_id FROM boxes WHERE projektnummer = %s", (projektnummer,))
        location = cursor.fetchone()
        if location:
            location_id = location[0]
            cursor.execute("DELETE FROM boxes WHERE projektnummer = %s", (projektnummer,))
            cursor.execute("UPDATE storage_locations SET belegt = FALSE WHERE id = %s", (location_id,))
            conn.commit()
            message = f"Kiste mit Projektnummer {projektnummer} wurde gelöscht."
        else:
            message = "Kiste nicht gefunden."
        
        # Fetch updated boxes list
        boxes = fetch_boxes(cursor)
        storage_locations = fetch_storage_locations(cursor)
        
        cursor.close()
        conn.close()
        
        return render_template('manage.html', message=message, highlight=None, boxes=boxes, storage_locations=storage_locations)
    else:
        return "Database connection failed."

@app.route('/edit_box/<projektnummer>', methods=['GET', 'POST'])
def edit_box(projektnummer):
    if request.method == 'POST':
        # Handle form submission for editing box
        pass
    else:
        # Render form for editing box
        pass

@app.route('/testansicht')
def testansicht():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        boxes = fetch_boxes(cursor)
        storage_locations = fetch_storage_locations(cursor)
        cursor.close()
        conn.close()
        return render_template('testansicht.html', boxes=boxes, storage_locations=storage_locations, highlight=None)
    else:
        return "Database connection failed."

if __name__ == '__main__':
    app.run(host='0.0.0.0')
