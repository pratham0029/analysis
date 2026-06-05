import snowflake.connector

def get_snowflake_connection(account, user):
    try:
        clean_account = account.replace(".snowflakecomputing.com", "").replace("https://", "")
        conn = snowflake.connector.connect(
            account=clean_account,
            user=user,
            authenticator='externalbrowser',
            warehouse='VIZ_UTIL_SMALL_WH',
            role='PUBLIC'
        )
        return conn
    except Exception as e:
        raise Exception(f"Snowflake SSO Connection Failed: {str(e)}")

def fetch_databases(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("SHOW DATABASES")
        return [row[1] for row in cursor.fetchall()]
    finally:
        cursor.close()

def fetch_schemas(conn, database):
    cursor = conn.cursor()
    try:
        cursor.execute(f'SHOW SCHEMAS IN DATABASE "{database}"')
        return [row[1] for row in cursor.fetchall()]
    finally:
        cursor.close()

def fetch_tables(conn, database, schema):
    objects = []
    cursor = conn.cursor()
    try:
        cursor.execute(f'SHOW TABLES IN SCHEMA "{database}"."{schema}"')
        for t in cursor.fetchall():
            objects.append({"name": t[1], "type": "TABLE"})
            
        cursor.execute(f'SHOW VIEWS IN SCHEMA "{database}"."{schema}"')
        for v in cursor.fetchall():
            objects.append({"name": v[1], "type": "VIEW"})
            
        return objects
    except Exception:
        return []
    finally:
        cursor.close()

def extract_table_metadata(conn, database, schema, tables):
    metadata = {}
    cursor = conn.cursor()
    try:
        for table in tables:
            table_data = {}
            
            cursor.execute(f'DESCRIBE TABLE "{database}"."{schema}"."{table}"')
            columns = cursor.fetchall()
            col_names = [col[0] for col in columns]
            table_data["schema"] = [{"column": col[0], "type": col[1]} for col in columns]
            
            try:
                cursor.execute(f'SELECT * FROM "{database}"."{schema}"."{table}" TABLESAMPLE (100) LIMIT 20')
                sample_rows = cursor.fetchall()
                table_data["sample_data"] = [dict(zip(col_names, row)) for row in sample_rows]
            except Exception as e:
                print(f"Warning: Could not fetch sample data for {table}. Reason: {e}")
                table_data["sample_data"] = []
                
            metadata[table] = table_data
            
        return metadata
    finally:
        cursor.close()