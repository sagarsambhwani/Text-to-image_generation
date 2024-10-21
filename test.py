import mysql.connector
from mysql.connector import Error

try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Centralperk2=",
        database="image_gen_app"
    )
    if db.is_connected():
        cursor = db.cursor()
        cursor.execute("SHOW TABLES")
        for table in cursor:
            print(table)
except Error as e:
    print(f"Error: {e}")
finally:
    if db.is_connected():
        cursor.close()
        db.close()
