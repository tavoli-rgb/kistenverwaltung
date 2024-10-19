from flask import Flask, request, render_template, redirect, url_for
import mysql.connector
import os
import logging

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', 'example'),
        host=os.getenv('DB_HOST', 'mysql'),
        database=os.getenv('DB_NAME', 'lagerverwaltung')
    )

def fetch_all_boxes(cursor):
    cursor.execute("""
        SELECT boxes.projektnummer, storage_locations.reihe, storage_locations.fach
        FROM boxes
        JOIN storage_locations ON boxes.lagerplatz_id = storage_locations.id
    """)
    return cursor.fetchall()

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        boxes = fetch_all_boxes(cursor)
    except mysql.connector.Error as err:
        return render_template('index.html', boxes=[], message=f"Error: {err}", highlight=None)
    finally:
        cursor.close()
        conn.close()
    return render_template('index.html', boxes=boxes, message=None, highlight=None)

@app.route('/find', methods=['POST'])
def find_box():
    projektnummer = request.form['projektnummer']
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT lagerplatz_id FROM boxes WHERE projektnummer = %s", (projektnummer,))
        location = cursor.fetchone()
        boxes = fetch_all_boxes(cursor)
        if location:
            cursor.execute("SELECT fach, reihe FROM storage_locations WHERE id = %s", (location[0],))
            place = cursor.fetchone()
            return render_template('index.html', message=f"Kiste mit Projektnummer {projektnummer} befindet sich an Fach {place[0]}, Reihe {place[1]}", highlight=(place[1], place[0]), boxes=boxes)
        else:
            return render_template('index.html', message="Kiste nicht gefunden.", highlight=None, boxes=boxes)
    except mysql.connector.Error as err:
        return render_template('index.html', boxes=[], message=f"Error: {err}", highlight=None)
    finally:
        cursor.close()
        conn.close()

@app.route('/manage', methods=['POST'])
def manage_boxes():
    message = None
    highlight = None
    projektnummer = request.form['projektnummer']
    action = request.form['action']
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if action == 'add':
            cursor.execute("SELECT COUNT(*) FROM boxes WHERE projektnummer = %s", (projektnummer,))
            count = cursor.fetchone()[0]
            if count > 0:
                message = "Projektnummer existiert bereits."
            else:
                cursor.execute("SELECT id FROM storage_locations WHERE belegt = FALSE LIMIT 1")
                location = cursor.fetchone()
                if location:
                    location_id = location[0]
                    cursor.execute("INSERT INTO boxes (projektnummer, lagerplatz_id) VALUES (%s, %s)", (projektnummer, location_id))
                    cursor.execute("UPDATE storage_locations SET belegt = TRUE WHERE id = %s", (location_id,))
                    conn.commit()
                    message = f"Kiste mit Projektnummer {projektnummer} wurde Lagerplatz {location_id} zugewiesen."
                    cursor.execute("SELECT fach, reihe FROM storage_locations WHERE id = %s", (location_id,))
                    place = cursor.fetchone()
                    highlight = (place[1], place[0])
                else:
                    message = "Kein freier Lagerplatz verfügbar."
        elif action == 'delete':
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
    except mysql.connector.Error as err:
        message = f"Error: {err}"
    finally:
        cursor.close()
        conn.close()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        boxes = fetch_all_boxes(cursor)
    except mysql.connector.Error as err:
        return render_template('index.html', boxes=[], message=f"Error: {err}", highlight=None)
    finally:
        cursor.close()
        conn.close()
    
    return render_template('index.html', message=message, highlight=highlight, boxes=boxes)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(host='0.0.0.0')
