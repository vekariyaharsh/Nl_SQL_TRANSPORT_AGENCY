import pandas as pd

FILE_PATH = r"C:\Users\dell\Downloads\Dump_Register.csv"
MAX_COLUMNS = 100

print("Reading CSV...")
df_temp = pd.read_csv(FILE_PATH, nrows=0)
all_columns = df_temp.columns.tolist()

print(f"\nTotal columns: {len(all_columns)}")
print("\nFirst 10 ORIGINAL column names:")
for i, col in enumerate(all_columns[:10], 1):
    print(f"{i}. '{col}' (has newline: {repr(col)})")

# Now read with selected columns
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

# Clean column names
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

print("\n\nFirst 10 CLEANED column names:")
for i, col in enumerate(df.columns[:10], 1):
    print(f"{i}. {col}")

print(f"\n\nTotal rows: {len(df)}")
print("Sample data (first row):")
print(df.iloc[0])
