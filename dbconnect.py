import mysql.connector
from db_config import DB_CONFIG
from contextlib import contextmanager

# connect mysql
@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        yield conn
        conn.commit()
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        print(f"Database process interruption:{err}")
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()
def  test():
    print("start connect mysql...")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE();")
        result = cursor.fetchone()
        print(f"The current connected database is: {result[0]}")

        cursor.close()
        print("test finished")


if __name__ == "__main__":
    test()
            
