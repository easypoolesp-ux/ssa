from django.db.backends.postgresql import base
from google.cloud.sql.connector import Connector, IPTypes
import os

class DatabaseWrapper(base.DatabaseWrapper):
    def get_new_connection(self, conn_params):
        # Remove 'creator' if it's there to avoid psycopg2 error
        conn_params.pop('creator', None)
        
        connector = Connector()
        return connector.connect(
            os.environ.get("DB_HOST").replace("/cloudsql/", ""),
            "pg8000",
            user=os.environ.get("DB_USER"),
            db=os.environ.get("DB_NAME"),
            enable_iam_auth=True,
            ip_type=IPTypes.PUBLIC
        )
