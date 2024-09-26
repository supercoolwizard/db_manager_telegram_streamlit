import sqlite3
import pandas as pd
from io import BytesIO


class SQLViewer:
    def __init__(self, database_name):
        self.connection = sqlite3.connect(database_name)
        self.cursor = self.connection.cursor()

    def simple_view(self, query):
        """Execute a query and return the raw results (used for table listing)."""
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def executor(self, query):
        try:
            self.cursor.execute(query)
            self.connection.commit()
        except Exception as e:
            raise RuntimeError(f"Query failed: {str(e)}")

    def view_query_as_df(self, query):
        df = pd.read_sql(query, self.connection)
        return df

    def export_query_to_csv(self, query):
        """Execute a query, convert the result to a CSV in memory, and return a BytesIO object."""
        df = pd.read_sql(query, self.connection)
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return output

    # def __del__(self):
    #     self.connection.close()

