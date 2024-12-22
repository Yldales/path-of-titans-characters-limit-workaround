import os
import json
import zipfile
import argparse
from datetime import datetime

CHARACTERS_LIMIT = 50
CHARACTERS_PATH = './Character'
PLAYERS_PATH = './Account'
SORT_OPTIONS = ["marks", "actualGrowth", "lastPlayedDate"]
TRIMMED_CHARACTERS_PATH = './TrimmedCharacters'

#=============================================================================#
# JSON LOAD/SAVE
#=============================================================================#

def load_json(file_path):
    """Load a JSON file and return its content."""
    with open(file_path, 'rb') as file:
        content = file.read()
    try:
        return json.loads(content.decode('utf-8'))
    except UnicodeDecodeError:
        print(f"Error decoding {file_path}. Skipping.")
        return {}

def save_json(data, file_path):
    """Save a JSON object to a file."""
    if args.simulate:
        print(f"Simulating save for {file_path}.")
        return
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

#=============================================================================#
# HELPER METHODS
#=============================================================================#

def backup():
    """Create a backup of the players and characters data."""
    """The backup will be saved in a ZIP file with the current date and time."""
    """Used before trimming the characters to respect the CHARACTERS_LIMIT."""
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{date_str}.zip"
    
    with zipfile.ZipFile(backup_filename, 'w') as backup_zip:
        for folder in [PLAYERS_PATH, CHARACTERS_PATH]:
            for root, _, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    backup_zip.write(file_path, os.path.relpath(file_path, os.path.join(folder, '..')))
    print(f"Backup created: {backup_filename}")

def get_player_files(path):
    """Return a list of player files in the specified path."""
    return [os.path.join(path, f) for f in os.listdir(path) if f.endswith('.json')]

def confirm_action(action):
    response = input(f"Are you sure you want to {action}? (yes/no): ").strip().lower()
    return response == 'yes' or response == 'y'

#=============================================================================#
# METHODS
#=============================================================================#

def restore():
    
    if not os.path.exists(TRIMMED_CHARACTERS_PATH):
        print("The trimmed characters folder does not exist.")
        return

    if not os.listdir(TRIMMED_CHARACTERS_PATH):
        print("The trimmed characters folder is empty.")
        return

    # We iterate over the player files in the PLAYERS_PATH.
    for player_file in get_player_files(PLAYERS_PATH):

        # We load the player file and its trimmed characters file.
        player_data = load_json(player_file)
        trimmed_file_path = os.path.join(TRIMMED_CHARACTERS_PATH, os.path.basename(player_file))
        
        # If the TRIMMED_CHARACTERS_PATH/<player_file>.json file exists, we restore the trimmed characters.
        if os.path.exists(trimmed_file_path):

            # We load the TRIMMED_CHARACTERS_PATH/<player_file>.json file.
            trimmed_data = load_json(trimmed_file_path)

            # We track the count of : characters in the player file, trimmed characters.
            current_characters_count = len(player_data.get('characters', []))
            trimmed_characters_count = len(trimmed_data.get('trimmed_characters', []))

            # We (re)add the trimmed characters to the player file and save it.
            player_data['characters'].extend(trimmed_data.get('trimmed_characters', []))
            save_json(player_data, player_file)
            print(f"Restored {trimmed_characters_count} trimmed characters to {os.path.basename(player_file)}.")

            # We remove the TRIMMED_CHARACTERS_PATH/<player_file>.json file to avoid restoring it again.
            os.remove(trimmed_file_path)

def trim_characters(player_file, sort_by):
    player_data = load_json(player_file)
    characters = player_data.get('characters', [])

    if len(characters) <= CHARACTERS_LIMIT:
        print(f"{player_file} [Character(s): {len(characters)}] - Skipping.")
        return
    print(f"{player_file} [Character(s): {len(characters)}] - Processing.")

    character_files = [os.path.join(CHARACTERS_PATH, f"{char_id}.json") for char_id in characters]
    character_data = [(load_json(char_file), char_file) for char_file in character_files]
    
    character_data.sort(key=lambda x: x[0].get(sort_by, 0), reverse=True)
    
    trimmed_characters = character_data[CHARACTERS_LIMIT:]
    trimmed_character_ids = [os.path.splitext(os.path.basename(char_file))[0] for _, char_file in trimmed_characters]
    
    for index, (char, _) in enumerate(character_data):
        status = "KEPT" if index < CHARACTERS_LIMIT else "TRIMMED"
        print(f" → [{status}] {char.get('characterName', 'Unknown')} - {sort_by.capitalize()}: {char.get(sort_by, 0)}")
    
    player_data['characters'] = [os.path.splitext(os.path.basename(char_file))[0] for _, char_file in character_data[:CHARACTERS_LIMIT]]
    save_json(player_data, player_file)

    if not os.path.exists(TRIMMED_CHARACTERS_PATH):
        os.makedirs(TRIMMED_CHARACTERS_PATH)
    
    trimmed_file_path = os.path.join(TRIMMED_CHARACTERS_PATH, os.path.basename(player_file))
    save_json({'trimmed_characters': trimmed_character_ids}, trimmed_file_path)

#=============================================================================#
# MAIN
#=============================================================================#

def main():
    global args
    parser = argparse.ArgumentParser(description="Path of Titans Characters Limit Workaround")
    parser.add_argument('--backup', action='store_true', help="Trim the characters to respect the CHARACTERS_LIMIT.")
    parser.add_argument('--restore', action='store_true', help="Restore the trimmed characters.")
    parser.add_argument('--sort-by', choices=SORT_OPTIONS, default='marks', help="Sort characters by the specified attribute.")
    parser.add_argument('--simulate', action='store_true', help="Simulate the trimming process without modifying the files.")
    args = parser.parse_args()

    if args.backup:
        if confirm_action("create a backup"):
            backup()
            main_process(args.sort_by)
    elif args.restore:
        if confirm_action("restore trimmed characters"):
            restore()
    else:
        parser.print_help()

def main_process(sort_by):
    player_files = get_player_files(PLAYERS_PATH)
    for player_file in player_files:
        trim_characters(player_file, sort_by)

if __name__ == "__main__":
    main()