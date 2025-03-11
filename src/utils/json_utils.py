import json
import os

def write_json_file(new_entry, file_path):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Load existing data if the file exists
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if not isinstance(data, list):  # Ensure it's a list
                    data = [data]
            except json.JSONDecodeError:
                data = []  # Reset if JSON is corrupted
    else:
        data = []  # Start with an empty list if the file doesn't exist or is empty

    # Append new data to the list
    data.append(new_entry)

    # Write updated JSON data back to the file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def read_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data[-1]