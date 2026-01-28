import pandas as pd
import mysql.connector
from sqlalchemy import create_engine, text
import pymysql
import warnings
warnings.filterwarnings('ignore')

# -----------------------------
# 1. File Config
# -----------------------------
FILE_PATH = r"C:\Users\dell\Downloads\Dump_Register.csv"
TABLE_NAME = "dump_register"
MAX_COLUMNS = 100
SKIP_FIRST_DATA_ROW = False

# -----------------------------
# 2. MySQL Config
# -----------------------------
MYSQL_USER = "root"
MYSQL_PASSWORD = "1234"
MYSQL_HOST = "localhost"
MYSQL_DATABASE = "test_harsh"

# -----------------------------
# 3. Read CSV
# -----------------------------
print("Reading CSV...")

try:
    df_temp = pd.read_csv(FILE_PATH, nrows=0)
    all_columns = df_temp.columns.tolist()

    print(f"Total columns in CSV: {len(all_columns)}")
    print(f"Limiting to first {MAX_COLUMNS} columns")

    selected_columns = all_columns[:MAX_COLUMNS]

    df = pd.read_csv(
        FILE_PATH, 
        usecols=selected_columns,
        low_memory=False,
        encoding='utf-8',
        quotechar='"',
        skipinitialspace=True,
        thousands=','
    )

    print(f"Loaded {len(df.columns)} columns and {len(df)} rows")
    
except Exception as e:
    print(f"Error reading CSV: {e}")
    exit(1)

# -----------------------------
# 4. Clean column names
# -----------------------------
print("\nCleaning column names...")

df.columns = [
    str(c).strip()
    .replace("\n", "_")
    .replace("\r", "_")
    .replace("\t", "_")
    .replace(" ", "_")
    .replace("-", "_")
    .replace(".", "_")
    .replace("(", "")
    .replace(")", "")
    .replace("/", "_")
    .replace("\\", "_")
    .replace("'", "")
    .replace('"', "")
    .replace(",", "")
    .replace("__", "_")
    .replace("___", "_")
    .strip("_")
    [:64]
    for c in df.columns
]

# Remove any remaining problematic characters
cleaned_columns = []
for col in df.columns:
    # Keep only alphanumeric and underscore
    clean_col = ''.join(c if c.isalnum() or c == '_' else '_' for c in col)
    # Remove consecutive underscores
    while '__' in clean_col:
        clean_col = clean_col.replace('__', '_')
    clean_col = clean_col.strip('_')
    
    # Ensure column name is not empty and doesn't start with a number
    if not clean_col or clean_col[0].isdigit():
        clean_col = 'col_' + clean_col
    
    cleaned_columns.append(clean_col)

df.columns = cleaned_columns

print("Column names cleaned")
print(f"\nFirst 10 column names:")
for i, col in enumerate(df.columns[:10], 1):
    print(f"   {i}. {col}")

# -----------------------------
# 5. Build SQL schema
# -----------------------------
dtype_mapping = {
    "int64": "BIGINT",
    "float64": "DOUBLE",
    "object": "TEXT",
    "datetime64[ns]": "DATETIME",
    "bool": "BOOLEAN",
    "Int64": "BIGINT"
}

columns_sql = []

print("\nBuilding SQL schema...")

for col, dtype in df.dtypes.items():
    sql_type = dtype_mapping.get(str(dtype), "TEXT")
    columns_sql.append(f"`{col}` {sql_type}")

schema_sql = ",\n".join(columns_sql)

create_table_sql = f"""
CREATE TABLE IF NOT EXISTS `{TABLE_NAME}` (
{schema_sql}
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

# -----------------------------
# 6. Create Table
# -----------------------------
print("\nCreating table in MySQL...")

try:
    connection = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset='utf8mb4'
    )
    cursor = connection.cursor()

    # Drop existing table
    cursor.execute(f"DROP TABLE IF EXISTS `{TABLE_NAME}`")
    print(f"Dropped existing table '{TABLE_NAME}' (if existed)")

    cursor.execute(create_table_sql)
    connection.commit()

    print("Table created successfully!")
    
    # Print schema
    print("\n" + "="*80)
    print(f"TABLE SCHEMA for '{TABLE_NAME}'")
    print("="*80)
    cursor.execute(f"DESCRIBE `{TABLE_NAME}`")
    schema_rows = cursor.fetchall()
    
    print(f"\n{'Column Name':<40} {'Data Type':<20} {'Null':<5} {'Key':<5}")
    print("-" * 80)
    for row in schema_rows[:15]:  # Show first 15 columns
        col_name, data_type, null, key, default, extra = row
        print(f"{col_name:<40} {data_type:<20} {null:<5} {key:<5}")
    if len(schema_rows) > 15:
        print(f"... and {len(schema_rows) - 15} more columns")
    print("="*80 + "\n")

except mysql.connector.Error as err:
    print(f"MySQL Error: {err}")
    exit(1)
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'connection' in locals():
        connection.close()

# -----------------------------
# 7. Skip first data row if needed
# -----------------------------
if SKIP_FIRST_DATA_ROW:
    print(f"\nSkipping first data row (contains schema info)")
    df = df.iloc[1:].reset_index(drop=True)
    print(f"Remaining rows: {len(df)}")

# -----------------------------
# 8. Process data
# -----------------------------
print("\nProcessing data...")

df = df.replace({pd.NA: None, pd.NaT: None})
df = df.where(pd.notnull(df), None)

# Convert problematic values
for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].astype(str).replace('nan', None).replace('None', None)

# -----------------------------
# 9. Insert data
# -----------------------------
print("\nInserting rows into MySQL...")

try:
    engine = create_engine(
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}?charset=utf8mb4",
        echo=False,
        pool_pre_ping=True,
        pool_recycle=3600
    )

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("Database connection successful")

    total_rows = len(df)
    chunk_size = 1000
    
    for i in range(0, total_rows, chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        chunk.to_sql(
            TABLE_NAME, 
            con=engine, 
            if_exists="append", 
            index=False, 
            chunksize=500,
            method='multi'
        )
        print(f"Inserted rows {i+1} to {min(i+chunk_size, total_rows)} of {total_rows}")

    print("\nData inserted successfully!")
    print(f"Total columns: {len(df.columns)}")
    print(f"Total rows inserted: {len(df)}")

except Exception as e:
    print(f"Error during insertion: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
finally:
    if 'engine' in locals():
        engine.dispose()

print("\nProcess completed!")
