import urllib.request
import urllib.error
import csv
import os
from pathlib import Path

SEASONS = ["2122", "2223", "2324", "2425", "2526"]
LEAGUES = {
    "E1": "championship",
    "E2": "league_one"
}
EXPECTED_MATCHES = 552
BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/{code}.csv"
RAW_DIR = Path("data/raw")

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    inventory_lines = []
    
    inventory_lines.append("## Raw Data Inventory")
    inventory_lines.append("")
    inventory_lines.append("| League | Season | File Name | Matches | Expected | Shortfall Reason |")
    inventory_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    
    for code, name in LEAGUES.items():
        print(f"--- Processing {name} ({code}) ---")
        for season in SEASONS:
            url = BASE_URL.format(season=season, code=code)
            filename = f"{name}_{season}.csv"
            filepath = RAW_DIR / filename
            
            print(f"Downloading {season} from {url}...")
            
            try:
                # Add headers to avoid 403 Forbidden on some servers
                req = urllib.request.Request(
                    url, 
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                
                with urllib.request.urlopen(req) as response:
                    content = response.read().decode('utf-8')
                    
                # Save file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                # Verify row count
                # Use splitlines to count rows. Note: some csv files have trailing blank lines.
                lines = [line for line in content.splitlines() if line.strip()]
                
                if not lines:
                    print(f"ERROR: File {filename} is empty!")
                    continue
                    
                match_count = len(lines) - 1 # Exclude header
                
                shortfall = EXPECTED_MATCHES - match_count
                reason = "None"
                
                if shortfall == 0:
                    status = "[OK] Perfect"
                elif shortfall > 0:
                    status = f"[WARN] Short by {shortfall}"
                    reason = "Requires DATA-4 verification (abandoned/postponed/Covid)"
                else:
                    status = f"[FAIL] Over by {abs(shortfall)}"
                    reason = "Requires manual check (duplicates?)"
                    
                print(f"  Saved {filename}: {match_count} matches. {status}")
                
                inventory_lines.append(f"| {name.capitalize()} | {season} | `{filename}` | {match_count} | {EXPECTED_MATCHES} | {reason} |")
                
            except urllib.error.URLError as e:
                print(f"ERROR downloading {url}: {e}")
                inventory_lines.append(f"| {name.capitalize()} | {season} | N/A | N/A | {EXPECTED_MATCHES} | Download Failed: {e} |")
                
    inventory_md = "\n".join(inventory_lines)
    
    print("\n--- INVENTORY MARKDOWN ---")
    print(inventory_md)
    print("--------------------------")
    
    # Write inventory output to a temp file for easy inclusion later
    with open("docs/temp_inventory_table.md", "w", encoding='utf-8') as f:
         f.write(inventory_md)

if __name__ == "__main__":
    main()
