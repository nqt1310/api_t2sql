import pandas as pd
from sqlalchemy import create_engine
from base.queries import DBQuery


class DBConnection:
    def __init__(self, db_type, db_name, db_user, db_password, db_host, port=None):
        self.db_type = db_type.lower()
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.port = port or (1521 if "oracle" in self.db_type else 5432)
        self.engine = self._create_engine()

    def _create_engine(self):
        if "postgres" in self.db_type:
            return create_engine(
                f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.port}/{self.db_name}"
            )
        elif "oracle" in self.db_type:
            return create_engine(
                f"oracle+oracledb://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.port}/{self.db_name}"
            )
        else:
            raise ValueError("Unsupported DB type")

    def exec_query_df(self, sql: str, params: dict | None = None) -> pd.DataFrame:
        """
        Execute SQL and return result as pandas DataFrame
        """
        with self.engine.connect() as conn:
            df = pd.read_sql(sql, conn, params=params)
        df.columns = [col.upper().strip() for col in df.columns]
        return df

    def get_raw_cursor(self):
        conn = self.engine.raw_connection()
        return conn, conn.cursor()
