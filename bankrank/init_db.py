# -*- coding: utf-8 -*-
"""
Database initialization script
"""
import pymysql

# Read the SQL file
with open('database/init.sql', 'r', encoding='utf-8') as f:
    sql_content = f.read()

# Connect to MySQL server (without database first)
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='123456',
    charset='utf8mb4'
)

try:
    cursor = conn.cursor()
    
    # Split by semicolons and execute each statement
    statements = sql_content.split(';')
    
    for statement in statements:
        statement = statement.strip()
        if statement and not statement.startswith('--'):
            try:
                cursor.execute(statement)
                conn.commit()
            except pymysql.Error as e:
                # Ignore duplicate entry errors for INSERT statements
                if e.args[0] != 1062:  # Duplicate entry error code
                    print(f"Warning: {e}")
    
    print("Database initialized successfully!")
    
finally:
    conn.close()
