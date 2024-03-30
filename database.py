import streamlit as st
import sqlite3
import pandas as pd


db_name = 'chatbot_roles.db'

def setup_database(db_name):
    # Verbindung zur Datenbank herstellen
    conn = sqlite3.connect(db_name, check_same_thread=False)
    c = conn.cursor()

    # Tabelle für Chatbot-Rollen erstellen, falls sie nicht existiert
    c.execute('''
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL
    )
    ''')

    # Änderungen an der Datenbank speichern und Verbindung schließen
    conn.commit()
    conn.close()

def connect_db(db_name):
    conn = sqlite3.connect(db_name, check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL
        )
        ''')
    return c, conn




# Funktionen für Datenbankoperationen
def get_role_names():
    c, conn = connect_db(db_name)
    c.execute('SELECT name FROM roles')
    return [row[0] for row in c.fetchall()]  # Nur Rollennamen zurückgeben
    conn.close()

def get_description_by_name(name):
    c, conn = connect_db(db_name)
    c.execute('SELECT description FROM roles WHERE name = ?', (name,))
    result = c.fetchone()
    return result[0] if result else "Beschreibung nicht gefunden."
    conn.close()

def insert_role(name, description):
    c, conn = connect_db(db_name)
    c.execute('INSERT INTO roles (name, description) VALUES (?, ?)', (name, description))
    conn.commit()
    conn.close()

def update_role(id, name, description):
    c, conn = connect_db(db_name)
    c.execute('UPDATE roles SET name = ?, description = ? WHERE id = ?', (name, description, id))
    conn.commit()
    conn.close()

def delete_role(id):
    c, conn = connect_db(db_name)
    c.execute('DELETE FROM roles WHERE id = ?', (id,))
    conn.commit()
    conn.close()

def get_all_roles():
    c, conn = connect_db(db_name)
    c.execute('SELECT id, name, description FROM roles')
    return c.fetchall()
    conn.close()