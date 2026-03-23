import pandas as pd
import os

base_path = "."   # FIXED

def load_json_folder(folder_name):
    folder_path = os.path.join(base_path, folder_name)
    
    all_files = os.listdir(folder_path)
    dataframes = []
    
    for file in all_files:
        if file.endswith(".jsonl"):
            file_path = os.path.join(folder_path, file)
            df = pd.read_json(file_path, lines=True)
            dataframes.append(df)
    
    return pd.concat(dataframes, ignore_index=True)


orders = load_json_folder("payments_accounts_receivable")


print("Columns:\n", orders.columns)
print("\nSample:\n", orders.head())