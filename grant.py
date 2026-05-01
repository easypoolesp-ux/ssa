import os
import pg8000
from google.cloud.sql.connector import Connector, IPTypes

def main():
    connector = Connector()

    def getconn() -> pg8000.dbapi.Connection:
        conn = connector.connect(
            "ssa-alumni:asia-south1:ssa-alumni-dev-db",
            "pg8000",
            user="postgres",
            password="TempPass123!",
            db="ssa_alumni_db",
            ip_type=IPTypes.PUBLIC,
        )
        return conn

    conn = getconn()
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        print("Executing grants...")
        cursor.execute('GRANT ALL ON SCHEMA public TO "ssa-alumni-dev-run-sa@ssa-alumni.iam";')
        cursor.execute('GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "ssa-alumni-dev-run-sa@ssa-alumni.iam";')
        cursor.execute('GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "ssa-alumni-dev-run-sa@ssa-alumni.iam";')
        cursor.execute('GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO "ssa-alumni-dev-run-sa@ssa-alumni.iam";')
        cursor.execute('ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "ssa-alumni-dev-run-sa@ssa-alumni.iam";')
        cursor.execute('ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "ssa-alumni-dev-run-sa@ssa-alumni.iam";')
        print("Grants applied successfully!")
    except Exception as e:
        print("Error:", e)
    finally:
        cursor.close()
        conn.close()
        connector.close()

if __name__ == "__main__":
    main()
