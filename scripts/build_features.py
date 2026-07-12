import sys
from pathlib import Path
import pandas as pd

# Add src to python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.features import generate_features

def main():
    champ_path = Path("data/processed/championship.csv")
    l1_path = Path("data/processed/league_one.csv")
    out_dir = Path("data/features")
    out_path = out_dir / "championship_features.csv"
    tmp_path = out_dir / "championship_features.csv.tmp"
    
    if not champ_path.exists() or not l1_path.exists():
        print("Error: Processed data files not found! Please run the data pipeline first.", file=sys.stderr)
        sys.exit(1)
        
    print("Loading processed datasets...")
    df_champ = pd.read_csv(champ_path)
    df_l1 = pd.read_csv(l1_path)
    
    print("Generating rolling form features (FEAT-1 and FEAT-2)...")
    df_features = generate_features(df_champ, df_l1)
    
    print(f"Creating output directory: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Atomically writing features to {out_path}...")
    if tmp_path.exists():
        tmp_path.unlink()
        
    df_features.to_csv(tmp_path, index=False)
    
    if out_path.exists():
        out_path.unlink()
    tmp_path.rename(out_path)
    
    print(f"Success! Generated features saved to {out_path}")
    print(f"Feature table dimensions: {df_features.shape[0]} rows × {df_features.shape[1]} columns")

if __name__ == "__main__":
    main()
