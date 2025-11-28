import os
import mysql.connector
from mysql.connector import Error
cfg = {
  'host': os.getenv('MYSQL_HOST','localhost'),
  'user': os.getenv('MYSQL_USER','admin2'),
  'password': os.getenv('MYSQL_PASSWORD','Newadmin7'),
  'database': os.getenv('MYSQL_DATABASE','talkia'),
  'port': int(os.getenv('MYSQL_PORT','3306'))
}
print('Connecting to MySQL with', cfg)
try:
    conn = mysql.connector.connect(**cfg)
    cur = conn.cursor()
    cur.execute('SHOW TABLES')
    print('Tables:', cur.fetchall())
    try:
        cur.execute('SELECT id, username FROM users')
        users = cur.fetchall()
        print('Users:', users)
    except Exception as e:
        print('No users table or error:', e)
    cur.close()
    conn.close()
except Error as e:
    print('MySQL connection error:', e)
