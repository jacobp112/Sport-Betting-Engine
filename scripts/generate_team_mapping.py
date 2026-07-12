import csv
import json
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
MAPPING_FILE = Path("docs/team_name_mapping.json")

# Predefined aliases to canonical names
ALIASES = {
    "Nott'm Forest": "Nottingham Forest",
    "Sheffield Utd": "Sheffield United",
    "Sheff Utd": "Sheffield United",
    "Sheffield Weds": "Sheffield Wednesday",
    "Sheff Weds": "Sheffield Wednesday",
    "West Brom": "West Bromwich Albion",
    "QPR": "Queens Park Rangers",
    "Cardiff": "Cardiff City",
    "Derby": "Derby County",
    "Hull": "Hull City",
    "Leeds": "Leeds United",
    "Leicester": "Leicester City",
    "Luton": "Luton Town",
    "Norwich": "Norwich City",
    "Oxford": "Oxford United",
    "Peterboro": "Peterborough United",
    "Peterborough": "Peterborough United",
    "Plymouth": "Plymouth Argyle",
    "Preston": "Preston North End",
    "Rotherham": "Rotherham United",
    "Stoke": "Stoke City",
    "Swansea": "Swansea City",
    "Wycombe": "Wycombe Wanderers",
    "Bolton": "Bolton Wanderers",
    "Burton": "Burton Albion",
    "Cambridge": "Cambridge United",
    "Cheltenham": "Cheltenham Town",
    "Exeter": "Exeter City",
    "Fleetwood": "Fleetwood Town",
    "Lincoln": "Lincoln City",
    "Northampton": "Northampton Town",
    "Shrewsbury": "Shrewsbury Town",
    "Wigan": "Wigan Athletic",
    "Carlisle": "Carlisle United",
    "Blackburn": "Blackburn Rovers",
    "Coventry": "Coventry City",
    "Ipswich": "Ipswich Town",
    "Accrington": "Accrington Stanley",
    "Milwall": "Millwall", # Just in case of raw data typo, map to correct spelling
    "Bristol C": "Bristol City",
    "Bristol R": "Bristol Rovers",
    "Forest Green": "Forest Green Rovers",
    "MK Dons": "Milton Keynes Dons",
    "Crewe": "Crewe Alexandra",
    "Doncaster": "Doncaster Rovers",
    "Gillingham": "Gillingham",
    "Wimbledon": "AFC Wimbledon",
    "Morecambe": "Morecambe",
    "Fleetwood": "Fleetwood Town",
    "Colchester": "Colchester United",
    "Harrogate": "Harrogate Town",
    "Sutton": "Sutton United",
    "Hartlepool": "Hartlepool United",
    "Oldham": "Oldham Athletic",
    "Scunthorpe": "Scunthorpe United",
    "Salford": "Salford City",
    "Grimsby": "Grimsby Town",
    "Stockport": "Stockport County",
    "Mansfield": "Mansfield Town",
    "Crawley": "Crawley Town",
    "Wrexham": "Wrexham",
    "Birmingham": "Birmingham City"
}

def main():
    unique_teams = set()
    
    for league in ["championship", "league_one"]:
        filepath = PROCESSED_DIR / f"{league}.csv"
        if not filepath.exists():
            print(f"File {filepath} not found.")
            continue
            
        print(f"Scanning {filepath} for team names...")
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                home = row.get("HomeTeam")
                away = row.get("AwayTeam")
                if home:
                    unique_teams.add(home.strip())
                if away:
                    unique_teams.add(away.strip())
                    
    print(f"Found {len(unique_teams)} unique raw team names.")
    
    # Build complete mapping dictionary
    mapping = {}
    
    # First pass: map raw team names to canonical names using ALIASES
    for raw_name in sorted(unique_teams):
        canonical_name = ALIASES.get(raw_name, raw_name)
        mapping[raw_name] = canonical_name
        
    # Second pass: ensure every canonical name also maps to itself
    canonical_names = set(mapping.values())
    for canonical in canonical_names:
        if canonical not in mapping:
            mapping[canonical] = canonical
            
    # Also ensure all predefined aliases are self-mapped if they are canonical
    for canonical in ALIASES.values():
        mapping[canonical] = canonical
        
    # Write sorted mapping to JSON
    sorted_mapping = {k: mapping[k] for k in sorted(mapping.keys())}
    
    MAPPING_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted_mapping, f, indent=2)
        
    print(f"Successfully generated {MAPPING_FILE} with {len(sorted_mapping)} entries.")

if __name__ == "__main__":
    main()
