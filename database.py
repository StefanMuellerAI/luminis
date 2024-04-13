import sqlite3
from contextlib import contextmanager

db_name = 'chatbot_roles.db'

@contextmanager
def connect_db(db_name):
    conn = sqlite3.connect(db_name, check_same_thread=False)
    c = conn.cursor()
    try:
        yield c
    finally:
        conn.commit()
        conn.close()

def validate_input(name, description, ai_model):
    if not (isinstance(name, str) and isinstance(description, str) and isinstance(ai_model, str)):
        raise ValueError("Alle Eingaben müssen vom Typ str sein")
    if not (0 < len(name) <= 100 and 0 < len(description) <= 300 and 0 < len(ai_model) <= 100):
        raise ValueError("Eingaben überschreiten zulässige Längenbeschränkungen")

def setup_database(db_name):
    # Verbindung zur Datenbank herstellen
    with connect_db(db_name) as c:

    # Tabelle für Chatbot-Rollen erstellen, falls sie nicht existiert
        c.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            ai_model TEXT NOT NULL
        )
        ''')
# Funktionen für Datenbankoperationen
def get_role_names():
    with connect_db(db_name) as c:
        c.execute('SELECT name FROM roles')
        return [row[0] for row in c.fetchall()]  # Nur Rollennamen zurückgeben

def role_name_exists(name):
    with connect_db(db_name) as c:
        # Boolean zurückgeben, ob der Rollenname bereits existiert
        c.execute('SELECT EXISTS(SELECT 1 FROM roles WHERE name = ?)', (name,))
        return c.fetchone()[0] == 1

def get_description_by_name(name):
    with connect_db(db_name) as c:
        c.execute('SELECT description FROM roles WHERE name = ?', (name,))
        result = c.fetchone()
        return result[0] if result else "Beschreibung nicht gefunden."

def get_aimodel_by_name(name):
    with connect_db(db_name) as c:
        c.execute('SELECT ai_model FROM roles WHERE name = ?', (name,))
        result = c.fetchone()
        return result[0] if result else "Beschreibung nicht gefunden."

def insert_role(name, description, ai_model):
    validate_input(name, description, ai_model)
    with connect_db(db_name) as c:
        c.execute('INSERT INTO roles (name, description, ai_model) VALUES (?, ?, ?)', (name, description, ai_model))

def update_role(id, name, description):
    validate_input(id, name, description)
    with connect_db(db_name) as c:
        c.execute('UPDATE roles SET name = ?, description = ? WHERE id = ?', (name, description, id))

def delete_role(name):
    with connect_db(db_name) as c:
        c.execute('DELETE FROM roles WHERE name = ?', (name,))

def list_roles():
    with connect_db(db_name) as c:
        c.execute('SELECT id, name, description, ai_model FROM roles')
        return c.fetchall()

