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
        boxes = fetch_boxes(cursor)
        storage_locations = fetch_storage_locations(cursor)
        if location:
            cursor.execute("SELECT fach, reihe FROM storage_locations WHERE id = %s", (location[0],))
            place = cursor.fetchone()
            cursor.close()
            conn.close()
            return render_template('index.html', message=f"Kiste mit Projektnummer {projektnummer} befindet sich an Fach {place[0]}, Reihe {place[1]}", highlight=(place[1], place[0]), boxes=boxes, storage_locations=storage_locations)
        else:
            cursor.close()
            conn.close()
            return render_template('index.html', message="Kiste nicht gefunden.", highlight=None, boxes=boxes, storage_locations=storage_locations)
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

@app.route('/manage', methods=['GET', 'POST'])
def manage_boxes():
    message = None
    highlight = None
    print_script = None
    
    if request.method == 'POST':
        projektnummer = request.form['projektnummer']
        kunde = request.form.get('kunde', None)
        action = request.form['action']
        conn = get_db_connection()
        if conn:
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
                        cursor.execute("INSERT INTO boxes (projektnummer, kunde, lagerplatz_id) VALUES (%s, %s, %s)", (projektnummer, kunde, location_id))
                        cursor.execute("UPDATE storage_locations SET belegt = TRUE WHERE id = %s", (location_id,))
                        conn.commit()
                        message = f"Kiste mit Projektnummer {projektnummer} wurde Lagerplatz {location_id} zugewiesen."
                        cursor.execute("SELECT fach, reihe FROM storage_locations WHERE id = %s", (location_id,))
                        place = cursor.fetchone()
                        highlight = (place[1], place[0])
                        print_script = f"window.open('/print_label/{projektnummer}/{kunde}/{place[1]}/{place[0]}', '_blank');"
                    else:
                        message = "Kein freier Lagerplatz verfügbar."
            cursor.close()
            conn.close()
        else:
            message = "Database connection failed."

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        boxes = fetch_boxes(cursor)
        storage_locations = fetch_storage_locations(cursor)
        cursor.close()
        conn.close()
        return render_template('manage.html', message=message, highlight=highlight, boxes=boxes, storage_locations=storage_locations, print_script=print_script)
    else:
        return "Database connection failed."

@app.route('/edit_box/<projektnummer>', methods=['GET', 'POST'])
def edit_box(projektnummer):
    conn = get_db_connection()
    if request.method == 'POST':
        kunde = request.form['kunde']
        box_id = request.form['box_id']
        if conn:
            cursor = conn.cursor()
            # Überprüfen, ob die Boxnummer bereits einer anderen Projektnummer zugeordnet ist
            cursor.execute("SELECT COUNT(*) FROM boxes WHERE lagerplatz_id = %s AND projektnummer != %s", (box_id, projektnummer))
            count = cursor.fetchone()[0]
            if count > 0:
                message = "Boxnummer ist bereits einer anderen Projektnummer zugeordnet."
                cursor.execute("""
                    SELECT boxes.projektnummer, boxes.kunde, storage_locations.id
                    FROM boxes
                    JOIN storage_locations ON boxes.lagerplatz_id = storage_locations.id
                    WHERE boxes.projektnummer = %s
                """, (projektnummer,))
                box = cursor.fetchone()
                cursor.close()
                conn.close()
                return render_template('edit_box.html', box=box, message=message)
            else:
                # Freigeben des bisherigen Lagerorts
                cursor.execute("SELECT lagerplatz_id FROM boxes WHERE projektnummer = %s", (projektnummer,))
                old_location_id = cursor.fetchone()[0]
                cursor.execute("UPDATE storage_locations SET belegt = FALSE WHERE id = %s", (old_location_id,))
                
                # Aktualisieren der Boxinformationen und Markieren des neuen Lagerorts als belegt
                cursor.execute("""
                    UPDATE boxes
                    SET kunde = %s, lagerplatz_id = %s
                    WHERE projektnummer = %s
                """, (kunde, box_id, projektnummer))
                cursor.execute("UPDATE storage_locations SET belegt = TRUE WHERE id = %s", (box_id,))
                
                conn.commit()
                cursor.close()
                conn.close()
                return '''
                    <script>
                        window.opener.location.reload();
                        window.close();
                    </script>
                '''
        else:
            return "Database connection failed."
    else:
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT boxes.projektnummer, boxes.kunde, storage_locations.id
                FROM boxes
                JOIN storage_locations ON boxes.lagerplatz_id = storage_locations.id
                WHERE boxes.projektnummer = %s
            """, (projektnummer,))
            box = cursor.fetchone()
            cursor.close()
            conn.close()
            if box:
                return render_template('edit_box.html', box=box)
            else:
                return "Box not found."
        else:
            return "Database connection failed."

if __name__ == '__main__':
    app.run(host='0.0.0.0')
