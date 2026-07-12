import os
import csv
import json
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
MAPPING_FILE = Path("docs/team_name_mapping.json")

def load_mapping():
    if not MAPPING_FILE.exists():
        raise FileNotFoundError(f"Mapping file not found at {MAPPING_FILE}. Run generate_team_mapping.py first.")
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_file(filepath, mapping):
    print(f"Normalising team names in {filepath}...")
    
    rows = []
    headers = []
    unmapped_teams = set()
    update_count = 0
    
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        for row in reader:
            home = row["HomeTeam"].strip()
            away = row["AwayTeam"].strip()
            
            # Map HomeTeam
            if home in mapping:
                mapped_home = mapping[home]
                if mapped_home != home:
                    update_count += 1
                row["HomeTeam"] = mapped_home
            else:
                unmapped_teams.add(home)
                
            # Map AwayTeam
            if away in mapping:
                mapped_away = mapping[away]
                if mapped_away != away:
                    update_count += 1
                row["AwayTeam"] = mapped_away
            else:
                unmapped_teams.add(away)
                
            rows.append(row)
            
    if unmapped_teams:
        print(f"  WARNING: Found unmapped teams in {filepath.name}: {unmapped_teams}")
    else:
        print(f"  All team names successfully matched in {filepath.name}.")
        
    # Write back to file
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"  Completed normalisation: {update_count} cells updated.")
    return len(unmapped_teams)

def main():
    mapping = load_mapping()
    print(f"Loaded {len(mapping)} mappings from {MAPPING_FILE}.")
    
    errors = 0
    for league in ["championship", "league_one"]:
        filepath = PROCESSED_DIR / f"{league}.csv"
        if filepath.exists():
            errors += normalize_file(filepath, mapping)
        else:
            print(f"File {filepath} not found.")
            
    if errors > 0:
        print(f"\nCompleted with {errors} unmatched team errors. Please update {MAPPING_FILE} and rerun.")
        exit(1)
    else:
        print("\nSuccess: Team name normalisation complete with zero errors.")

if __name__ == "__main__":
    main()
