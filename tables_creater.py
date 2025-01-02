import sqlite3

conn = sqlite3.connect('database.db')
conn.execute('''
CREATE TABLE IF NOT EXISTS STUDENTS(
  Id INT PRIMARY KEY,
  Name VARCHAR(20),
  age INT
  );
''')
conn.commit()
conn.close()