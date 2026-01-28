import pandas as pd
import mysql.connector
from sqlalchemy import create_engine, text
import pymysql
import warnings
import numpy as np

warnings.filterwarnings('ignore')

# -----------------------------
# 1. File Config
# -----------------------------
FILE_PATH = r"C:\Users\dell\Downloads\Dump_Register(2).csv"     # CSV file path
TABLE_NAME = "reg_dump"                                 # MySQL table name
SKIP_FIRST_DATA_ROW = False                                  

# -----------------------------
# 2. MySQL Config
# -----------------------------
MYSQL_USER = "root"
MYSQL_PASSWORD = "1234"
MYSQL_HOST = "localhost"
MYSQL_DATABASE = "test_harsh"

# -----------------------------
# 3. Target Schema Definition
# -----------------------------
# Maps column name -> expected type handling
TARGET_SCHEMA = {
    'sr_no': 'int',
    'cn_no': 'str',
    'cn_date': 'date',
    'cn_type': 'str',
    'lr_office': 'str',
    'billing_party': 'str',
    'route': 'str',
    'billing_office': 'str',
    'bill_no': 'str',
    'bill_date': 'date',
    'mr_no': 'str',
    'expected_date': 'date',
    'reach_date': 'date',
    'unload_date': 'date',
    'pod_date': 'date',
    'submission_date': 'date',
    'cn_doe': 'date',
    'origin': 'str',
    'destination': 'str',
    'vehicle_no': 'str',
    'vehicle_type': 'str',
    'load_type': 'str',
    'no_of_pieces': 'decimal',
    'actual_weight': 'decimal',
    'charge_weight': 'decimal',
    'basic_freight': 'decimal',
    'detention': 'decimal',
    'other_charges': 'decimal',
    'service_tax': 'decimal',
    'total_freight': 'decimal',
    'rounded_value': 'decimal',
    'total_plus_rounded': 'decimal',
    'payment_received': 'decimal',
    'deduction_lr': 'decimal',
    'balance': 'decimal',
    'extra_cost_lr': 'decimal',
    'hire_charges': 'decimal',
    'detention_hc': 'decimal',
    'unload_hc': 'decimal',
    'other_hc': 'decimal',
    'misc1_hc': 'decimal',
    'misc2_hc': 'decimal',
    'penalty_hc': 'decimal',
    'claims_hc': 'decimal',
    'other_ded_hc': 'decimal',
    'hire_hc': 'decimal',
    'own_hc': 'decimal',
    'lr_profit': 'decimal',
    'suppbill_amt': 'decimal',
    'no_of_hm': 'int',
    'hm_no': 'str',
    'consignor': 'str',
    'consignee': 'str',
    'invoice_no': 'str',
    'invoice_date': 'date',
    'materials': 'str',
    'cover_note_no': 'str',
    'pod_receipt_no': 'str',
    'pod_receipt_date': 'date',
    'cn_remark': 'str',
    'broker': 'str',
    'hire_vehicle_party': 'str',
    'hire_vehicle_no': 'str',
    'ref1': 'str',
    'ref2': 'str',
    'ref3': 'str',
    'ref4': 'str',
    'ref5': 'str',
    'percentage': 'decimal',
    'hm_bal_payment_office': 'str'
}

def clean_currency(x):
    """Clean currency/number strings"""
    if pd.isna(x) or x == '':
        return None
    if isinstance(x, (int, float)):
        return x
    # Remove currency symbols, commas, spaces
    clean = str(x).replace('₹', '').replace('$', '').replace(',', '').strip()
    try:
        if clean == '-' or clean == '.':
            return None
        return float(clean)
    except:
        return None

def parse_dates(x):
    """Robust date parsing"""
    if pd.isna(x) or x == '' or str(x).strip() == '-':
        return None
    try:
        return pd.to_datetime(x, errors='coerce')
    except:
        return None

# -----------------------------
# 4. Read and Process CSV
# -----------------------------
print("📥 Reading CSV...")

try:
    # Read CSV
    df = pd.read_csv(
        FILE_PATH, 
        low_memory=False,
        encoding='utf-8',
        quotechar='"',
        skipinitialspace=True,
        thousands=','  
    )
    
    # -----------------------------
    # 5. Clean Column Names
    # -----------------------------
    print("\n🧹 Cleaning column names...")
    
    # Create mapping of current clean names to original
    current_columns = {}
    for col in df.columns:
        # Standardize: lowercase, replace spaces/special chars with underscore
        clean = str(col).lower().strip().replace(' ', '_').replace('.', '_').replace('/', '_').replace('-', '_')
        # Remove consecutive underscores
        while '__' in clean:
            clean = clean.replace('__', '_')
        clean = clean.strip('_')
        current_columns[clean] = col

    # Rename dataframe columns to match target schema where possible
    final_df = pd.DataFrame()
    
    # Iterate through target schema and try to find matching columns
    matched_cols = 0
    missing_cols = []
    
    for target_col, dtype in TARGET_SCHEMA.items():
        if target_col in current_columns:
            original_col = current_columns[target_col]
            series = df[original_col]
            
            # Apply type conversion
            if dtype == 'decimal':
                final_df[target_col] = series.apply(clean_currency)
            elif dtype == 'date':
                final_df[target_col] = pd.to_datetime(series, errors='coerce')
            elif dtype == 'int':
                final_df[target_col] = pd.to_numeric(series, errors='coerce').fillna(0).astype('Int64')
            else: # str/text
                final_df[target_col] = series.astype(str).replace('nan', None).replace('None', None)
            
            matched_cols += 1
        else:
            print(f"⚠️ Warning: Target column '{target_col}' not found in CSV. Filling with NULL.")
            final_df[target_col] = None
            missing_cols.append(target_col)

    print(f"✅ Matched {matched_cols} columns out of {len(TARGET_SCHEMA)}")
    
    # -----------------------------
    # 6. Append to MySQL
    # -----------------------------
    print("\n🚀 Appending data to MySQL table: " + TABLE_NAME)
    
    # Create SQLAlchemy engine
    engine = create_engine(
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}?charset=utf8mb4",
        echo=False
    )
    
    # Insert data
    final_df.to_sql(
        TABLE_NAME,
        con=engine,
        if_exists='append', # CRITICAL: Append instead of replace
        index=False,
        chunksize=1000,
        method='multi'
    )
    
    print("\n🎉 Data inserted successfully!")
    print(f"📊 Total rows inserted: {len(final_df)}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    if 'engine' in locals():
        engine.dispose()