import os
import csv
from datetime import datetime
from pathlib import Path

SEASONS = ["2122", "2223", "2324", "2425", "2526"]
LEAGUES = {
    "championship": "championship",
    "league_one": "league_one"
}
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

BASE_COLS = ["Div", "Date", "Time", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR", "season", "clv_reference_book"]
OP_ODDS_COLS = ["B365H", "B365D", "B365A", "PSH", "PSD", "PSA", "AvgH", "AvgD", "AvgA", "MaxH", "MaxD", "MaxA"]
CL_ODDS_COLS = ["B365CH", "B365CD", "B365CA", "PSCH", "PSCD", "PSCA", "AvgCH", "AvgCD", "AvgCA", "MaxCH", "MaxCD", "MaxCA"]
AH_COLS = [
    "AHh", "B365AHH", "B365AHA", "PAHH", "PAHA", "AvgAHH", "AvgAHA", "MaxAHH", "MaxAHA",
    "AHCh", "B365CAHH", "B365CAHA", "PCAHH", "PCAHA", "AvgCAHH", "AvgCAHA", "MaxCAHH", "MaxCAHA"
]
ALL_COLS = BASE_COLS + OP_ODDS_COLS + CL_ODDS_COLS + AH_COLS

def parse_date(date_str):
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"Unknown date format: {date_str}")

def clean_value(val, col):
    val = val.strip()
    if not val:
        return ""
    try:
        num = float(val)
        # Check odds bounds to catch corrupted values (e.g. "22" in AH odds)
        is_1x2_odds = col in OP_ODDS_COLS or col in CL_ODDS_COLS
        is_ah_odds = col in AH_COLS and col not in ["AHh", "AHCh"]
        
        if is_1x2_odds:
            if not (1.01 <= num <= 50.0):
                return ""
        elif is_ah_odds:
            if not (1.01 <= num <= 5.0):
                return ""
                
        return str(num)
    except ValueError:
        pass
    return val

def process_league(league_name):
    print(f"\n--- Processing {league_name.capitalize()} ---")
    processed_rows = []
    
    total_rows = 0
    pinnacle_op_valid = 0
    pinnacle_cl_valid = 0
    b365_op_valid = 0
    b365_cl_valid = 0
    avg_op_valid = 0
    avg_cl_valid = 0
    max_op_valid = 0
    max_cl_valid = 0
    
    for season in SEASONS:
        filename = f"{league_name}_{season}.csv"
        filepath = RAW_DIR / filename
        
        if not filepath.exists():
            print(f"Skipping {filename} - not found.")
            continue
            
        print(f"Reading {filename}...")
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            
            # Check if headers we need exist in raw file
            headers = reader.fieldnames
            if not headers:
                print(f"Error: Empty headers in {filename}")
                continue
                
            # Check if Pinnacle exists (some older files might be missing them)
            # Normalise headers to avoid casing/spacing mismatches
            header_map = {h.strip(): h for h in headers}
            
            seen_keys = set()
            for row in reader:
                # Basic validation: must have HomeTeam and FTR
                home = row.get(header_map.get("HomeTeam", ""))
                if not home or not home.strip():
                    continue # Skip empty rows or footer noise
                    
                processed_row = {}
                
                # Base fields
                processed_row["Div"] = row.get(header_map.get("Div", "")).strip()
                processed_row["Date"] = parse_date(row.get(header_map.get("Date", "")).strip())
                processed_row["Time"] = row.get(header_map.get("Time", ""), "").strip()
                processed_row["HomeTeam"] = row.get(header_map.get("HomeTeam", "")).strip()
                processed_row["AwayTeam"] = row.get(header_map.get("AwayTeam", "")).strip()
                processed_row["FTHG"] = row.get(header_map.get("FTHG", "")).strip()
                processed_row["FTAG"] = row.get(header_map.get("FTAG", "")).strip()
                processed_row["FTR"] = row.get(header_map.get("FTR", "")).strip()
                processed_row["season"] = season
                
                # 1. Duplicate row check
                match_key = (processed_row["HomeTeam"], processed_row["AwayTeam"], processed_row["Date"])
                if match_key in seen_keys:
                    print(f"  WARNING: Duplicate row skipped: {match_key[0]} vs {match_key[1]} on {match_key[2]}")
                    continue
                seen_keys.add(match_key)
                
                # 2. Plausible goal range check (0-15) and type conversion
                try:
                    fthg_int = int(processed_row["FTHG"])
                    ftag_int = int(processed_row["FTAG"])
                except ValueError:
                    print(f"  WARNING: Skipped row due to non-numeric goals: {processed_row['HomeTeam']} vs {processed_row['AwayTeam']} on {processed_row['Date']} (FTHG={processed_row['FTHG']}, FTAG={processed_row['FTAG']})")
                    continue
                    
                if not (0 <= fthg_int <= 15) or not (0 <= ftag_int <= 15):
                    print(f"  WARNING: Skipped row due to goals out of range: {processed_row['HomeTeam']} vs {processed_row['AwayTeam']} on {processed_row['Date']} (FTHG={fthg_int}, FTAG={ftag_int})")
                    continue
                
                # 3. Cross-field consistency check (FTR must match FTHG vs FTAG difference)
                ftr = processed_row["FTR"]
                expected_ftr = "D"
                if fthg_int > ftag_int:
                    expected_ftr = "H"
                elif fthg_int < ftag_int:
                    expected_ftr = "A"
                    
                if ftr != expected_ftr:
                    print(f"  WARNING: Skipped row due to inconsistent FTR: {processed_row['HomeTeam']} vs {processed_row['AwayTeam']} on {processed_row['Date']} (FTHG={fthg_int}, FTAG={ftag_int}, FTR={ftr}, expected {expected_ftr})")
                    continue
                
                # Odds fields
                for col in OP_ODDS_COLS + CL_ODDS_COLS + AH_COLS:
                    raw_col = header_map.get(col)
                    val = row.get(raw_col, "") if raw_col else ""
                    processed_row[col] = clean_value(val, col)
                
                # Determine CLV Reference Book
                if processed_row["PSCH"] and processed_row["PSCD"] and processed_row["PSCA"]:
                    processed_row["clv_reference_book"] = "pinnacle"
                else:
                    processed_row["clv_reference_book"] = "market_average"
                
                # Verification counts
                total_rows += 1
                if processed_row["PSH"] and processed_row["PSD"] and processed_row["PSA"]:
                    pinnacle_op_valid += 1
                if processed_row["PSCH"] and processed_row["PSCD"] and processed_row["PSCA"]:
                    pinnacle_cl_valid += 1
                    
                if processed_row["B365H"] and processed_row["B365D"] and processed_row["B365A"]:
                    b365_op_valid += 1
                if processed_row["B365CH"] and processed_row["B365CD"] and processed_row["B365CA"]:
                    b365_cl_valid += 1
                    
                if processed_row["AvgH"] and processed_row["AvgD"] and processed_row["AvgA"]:
                    avg_op_valid += 1
                if processed_row["AvgCH"] and processed_row["AvgCD"] and processed_row["AvgCA"]:
                    avg_cl_valid += 1
                    
                if processed_row["MaxH"] and processed_row["MaxD"] and processed_row["MaxA"]:
                    max_op_valid += 1
                if processed_row["MaxCH"] and processed_row["MaxCD"] and processed_row["MaxCA"]:
                    max_cl_valid += 1
                
                processed_rows.append(processed_row)
                
    # Sort chronologically by date and time
    processed_rows.sort(key=lambda r: (r["Date"], r["Time"]))
    
    # Save output to a temp file first
    output_path = PROCESSED_DIR / f"{league_name}.csv"
    tmp_path = PROCESSED_DIR / f"{league_name}.csv.tmp"
    with open(tmp_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ALL_COLS)
        writer.writeheader()
        writer.writerows(processed_rows)
        
    print(f"Staged processed data to temporary file {tmp_path}")
    print(f"Total Matches: {total_rows}")
    
    pinnacle_op_rate = (pinnacle_op_valid / total_rows) * 100 if total_rows else 0
    pinnacle_cl_rate = (pinnacle_cl_valid / total_rows) * 100 if total_rows else 0
    b365_op_rate = (b365_op_valid / total_rows) * 100 if total_rows else 0
    b365_cl_rate = (b365_cl_valid / total_rows) * 100 if total_rows else 0
    avg_op_rate = (avg_op_valid / total_rows) * 100 if total_rows else 0
    avg_cl_rate = (avg_cl_valid / total_rows) * 100 if total_rows else 0
    max_op_rate = (max_op_valid / total_rows) * 100 if total_rows else 0
    max_cl_rate = (max_cl_rate_val := (max_cl_valid / total_rows) * 100 if total_rows else 0)
    
    # Calculate rates per season for diagnostics
    seasons_stats = {}
    for r in processed_rows:
        seas = r["season"]
        if seas not in seasons_stats:
            seasons_stats[seas] = {"total": 0, "pin_cl": 0, "pin_op": 0, "avg_cl": 0}
        seasons_stats[seas]["total"] += 1
        if r["PSH"] and r["PSD"] and r["PSA"]:
            seasons_stats[seas]["pin_op"] += 1
        if r["PSCH"] and r["PSCD"] and r["PSCA"]:
            seasons_stats[seas]["pin_cl"] += 1
        if r["AvgCH"] and r["AvgCD"] and r["AvgCA"]:
            seasons_stats[seas]["avg_cl"] += 1
            
    print("\n--- Per-Season Stats ---")
    for seas, stats in sorted(seasons_stats.items()):
        op_pct = (stats["pin_op"] / stats["total"]) * 100
        cl_pct = (stats["pin_cl"] / stats["total"]) * 100
        avg_pct = (stats["avg_cl"] / stats["total"]) * 100
        print(f"Season {seas}: Total={stats['total']}, Pinnacle Closing={cl_pct:.2f}%, Avg Closing={avg_pct:.2f}%")
        
    print(f"Pinnacle Opening Join Rate: {pinnacle_op_rate:.2f}%")
    print(f"Pinnacle Closing Join Rate: {pinnacle_cl_rate:.2f}%")
    print(f"Market Average Closing Join Rate: {avg_cl_rate:.2f}%")
    
    # Assert Market Average Closing meets 95%+ threshold
    assert avg_cl_rate >= 95.0, f"Error: Market Average closing odds join rate ({avg_cl_rate:.2f}%) is below the 95% threshold!"
    print("Assertion Passed: Market Average closing odds join rate >= 95%")
    
    # Assert Pinnacle Closing is 100% (>= 95%) for seasons 21/22 to 24/25
    for seas in ["2122", "2223", "2324", "2425"]:
        stats = seasons_stats.get(seas, {"total": 0, "pin_cl": 0})
        pct = (stats["pin_cl"] / stats["total"]) * 100 if stats["total"] else 0
        assert pct >= 95.0, f"Error: Season {seas} Pinnacle closing odds join rate ({pct:.2f}%) is below 95%!"
    print("Assertion Passed: Pinnacle closing odds join rate >= 95% for seasons 21/22 to 24/25")
    
    # Assert total match count matches formula: 552 matches per completed season
    expected_total_matches = 552 * len(SEASONS)
    assert total_rows == expected_total_matches, f"Error: Processed {total_rows} matches, but expected {expected_total_matches}!"
    print(f"Assertion Passed: Processed match count ({total_rows}) matches expected ({expected_total_matches})")
    
    if pinnacle_cl_rate < 95.0:
        print(f"WARNING: Overall Pinnacle closing odds join rate ({pinnacle_cl_rate:.2f}%) is below 95% due to 25/26 season collection gaps on football-data.co.uk.")
    
    # Rename tmp file to final file now that all assertions passed successfully
    if output_path.exists():
        output_path.unlink()
    tmp_path.rename(output_path)
    print(f"Atomically saved processed data to {output_path}")
    
    summary = {
        "league": league_name,
        "total": total_rows,
        "pinnacle_op": pinnacle_op_rate,
        "pinnacle_cl": pinnacle_cl_rate,
        "b365_op": b365_op_rate,
        "b365_cl": b365_cl_rate,
        "avg_op": avg_op_rate,
        "avg_cl": avg_cl_rate,
        "max_op": max_op_rate,
        "max_cl": max_cl_rate
    }
    return summary

def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    summaries = []
    
    for league in LEAGUES:
        summary = process_league(league)
        summaries.append(summary)
        
    # Generate documentation markdown
    doc_lines = []
    doc_lines.append("## Odds Verification and Join Rates (DATA-2)")
    doc_lines.append("")
    doc_lines.append("We verified the availability of opening and closing odds across Pinnacle, Bet365, Market Average, and Market Maximum.")
    doc_lines.append("Pinnacle serves as the primary sharp reference for de-vigging, and has a strict 95%+ coverage requirement.")
    doc_lines.append("")
    doc_lines.append("| League | Total Matches | Pinnacle Opening | Pinnacle Closing | Bet365 Opening | Bet365 Closing | Market Avg Opening | Market Avg Closing | Market Max Opening | Market Max Closing |")
    doc_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    
    for s in summaries:
        doc_lines.append(
            f"| {s['league'].capitalize()} | {s['total']} | {s['pinnacle_op']:.2f}% | {s['pinnacle_cl']:.2f}% | "
            f"{s['b365_op']:.2f}% | {s['b365_cl']:.2f}% | {s['avg_op']:.2f}% | {s['avg_cl']:.2f}% | "
            f"{s['max_op']:.2f}% | {s['max_cl']:.2f}% |"
        )
        
    doc_lines.append("")
    doc_lines.append("> [!NOTE]")
    doc_lines.append("> All processed data is cleaned, validated, and saved chronologically in `/data/processed/` with a uniform `season` and ISO date column.")
    
    doc_md = "\n".join(doc_lines)
    with open("docs/temp_odds_table.md", "w", encoding="utf-8") as f:
        f.write(doc_md)
        
    print("\n--- ODDS VERIFICATION MARKDOWN ---")
    print(doc_md)
    print("----------------------------------")

if __name__ == "__main__":
    main()
