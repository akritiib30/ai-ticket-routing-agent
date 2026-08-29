import pandas as pd

# Load dataset
df = pd.read_csv("tickets.csv")

print("\n===== DATASET OVERVIEW =====")
print("Total rows:", len(df))
print("Total columns:", len(df.columns))

print("\nColumns:")
print(df.columns.tolist())

print("\n===== MISSING VALUES =====")
print(df.isnull().sum())

print("\n===== DUPLICATE ROWS =====")
print("Duplicate rows:", df.duplicated().sum())

print("\n===== CATEGORY DISTRIBUTION =====")
print(df["category"].value_counts())

print("\n===== PRIORITY DISTRIBUTION =====")
print(df["priority"].value_counts())

print("\n===== SAMPLE TICKETS =====")

for i, row in df.head(10).iterrows():
    print("\nTicket", i + 1)
    print("Title:", row["title"])
    print("Description:", row["description"])
    print("Category:", row["category"])
    print("Priority:", row["priority"])
    print("Resolution:", row["resolution"])