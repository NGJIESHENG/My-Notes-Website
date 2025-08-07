import sqlite3
from pathlib import Path

db_path = Path("instance/user.db")

if not db_path.exists():
    print("Database file not found!")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get table info
cursor.execute("PRAGMA table_info(file)")
columns = cursor.fetchall()

print("Columns in 'file' table:")
print("-" * 40)
print("ID | Name          | Type    | NotNull | Default | PK")
print("-" * 40)
for col in columns:
    print(f"{col[0]:2} | {col[1]:13} | {col[2]:7} | {col[3]:7} | {col[4] or 'None':7} | {col[5]}")

conn.close()