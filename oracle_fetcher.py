import urllib.request, urllib.error
import sys
import json
import glob
import datetime
import os

PROGRAM_VERSION = "MTGCardSimilarity/0.1"
CARD_DATASET = "https://api.scryfall.com/bulk-data/oracle-cards"

# NOTE: Only ever requests a new file if one does not exist for the present day
# Retrieve the oracle json file of all cards and save it locally, returns the new file's name
def get_oracle_json() -> str:

    latest_file, latest_date = get_latest_local_oracle_json()
    if latest_file:
        deleted_files = delete_old_jsons(dir='card_data', pathname='oracle-cards-*.json', excluded_jsons=[latest_file])
        print(f"Deleted the following out-of-date files: {deleted_files}")

        # Return latest file if it's from today's date
        if latest_date.date() == datetime.datetime.now().date():
            return latest_file

    headers = { "User-Agent": PROGRAM_VERSION }
    initial_req = urllib.request.Request(CARD_DATASET, headers=headers)

    try:
        # Initial Request
        with urllib.request.urlopen(initial_req) as response:
            response_dict = json.loads(response.read().decode("utf-8"))

            update_time = response_dict.get("updated_at")
            if not update_time:
                raise ValueError("'updated_at' time data not found in response.")

            json_url = response_dict.get("download_uri")
            if not json_url:
                raise ValueError("JSON URL not found in response.")
            
        # JSON file Request
        json_req = urllib.request.Request(json_url, headers=headers)
        with urllib.request.urlopen(json_req) as response:
            data = response.read().decode("utf-8")
            json_object = json.loads(data)

            # Save cards to local json file, file name format: 'oracle-cards-2024-12-26T22_04_29.json'
            new_file_name = f"card_data/oracle-cards-{update_time.replace(":","_")[:19]}.json"
            with open(new_file_name, "w", encoding="utf-8") as json_file:
                json.dump(json_object, json_file)

    
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}", file=sys.stderr)
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}", file=sys.stderr)
    except ValueError as e:
        print(f"Value Error: {e}", file=sys.stderr)
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}", file=sys.stderr)

    
    return new_file_name


# Search for files that match the oracle cards name pattern, return the latest file name and datetime object
def get_latest_local_oracle_json() -> tuple[str, datetime.datetime]:
    oracle_json_files:list = glob.glob("card_data/oracle-cards-*-*-*T*_*_*.json")

    current_date = datetime.datetime.now()
    latest_date:datetime.datetime = None
    latest_file:str = None
    for fname in oracle_json_files:
        # Parse date data
        date_string:str = fname[13:-5]
        date_string = date_string.replace('_', ':')
        file_date = datetime.datetime.fromisoformat(date_string)

        # First file
        if latest_date == None:
            latest_date = file_date
            latest_file = fname
            continue
        
        diff = current_date - file_date
        if diff < (current_date - latest_date):
            latest_date = file_date
            latest_file = fname

    return latest_file, latest_date

# Delete all files that match a pattern
def delete_old_jsons(dir:str | None = None, pathname:str = "oracle-cards-*.json", excluded_jsons:list = []) -> list:
    """
    Deletes JSON files in a directory that match the pathname but are not in the excluded_jsons list.

    Parameters:
    - dir (str): Directory to look for files (default: None)
    - pathname (str): Pattern of file names to search for (default: 'oracle-cards-*.json')
    - excluded_jsons (list): List of file names to exclude from deletion.

    Returns:
    - list: List of deleted file paths.
    """

    # Normalize to full paths when there's a directory name present
    if dir:
        excluded_jsons = list(map(lambda x: os.path.join(dir, x), excluded_jsons))
        pathname = os.path.join(dir, pathname)
    
    json_list = glob.glob(pathname)
    files_to_delete = [file for file in json_list if file not in excluded_jsons]

    deleted = []
    for file in files_to_delete:
        try:
            os.remove(file)
            deleted.append(file)
        except Exception as e:
            print(f"Failed to delete {file}: {e}")

    return deleted


if __name__ == "__main__":
    fname = get_oracle_json()
    print(f"Oracle text of all cards successfully saved as '{fname}'")
