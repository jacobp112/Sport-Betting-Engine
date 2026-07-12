"""
Train Baseline Models (Epic 3: MODEL-1 through MODEL-5)

Trains the Independent Double Poisson GLM and Dynamic Elo models on
Championship data, evaluates on the Validation set (Season 24/25), and
quarantines the Test set (Season 25/26).
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.models.poisson import IndependentDoublePoissonGLM
from src.models.elo import EloTracker
from src.models.evaluate import brier_score, log_loss, accuracy, calibration_table, print_calibration_table


# --- Configuration ---
FEATURES_PATH = Path("data/features/championship_features.csv")

TRAIN_SEASONS = [2122, 2223, 2324]
VAL_SEASONS = [2425]
TEST_SEASONS = [2526]  # QUARANTINED -- do not touch during Epic 3

# Features used for predicting home goals (lambda)
HOME_GOAL_FEATURES = [
    "home_rolling_gs_5", "home_rolling_gs_10",
    "away_rolling_gc_5", "away_rolling_gc_10",
    "home_venue_rolling_gs_5", "home_venue_rolling_gs_10",
    "home_rolling_gd_5",
    "home_rest_days",
]

# Features used for predicting away goals (mu)
AWAY_GOAL_FEATURES = [
    "away_rolling_gs_5", "away_rolling_gs_10",
    "home_rolling_gc_5", "home_rolling_gc_10",
    "away_venue_rolling_gs_5", "away_venue_rolling_gs_10",
    "away_rolling_gd_5",
    "away_rest_days",
]


def main():
    # 1. Load feature table
    if not FEATURES_PATH.exists():
        print("Error: Feature table not found. Run scripts/build_features.py first.", file=sys.stderr)
        sys.exit(1)

    print("Loading feature table...")
    df = pd.read_csv(FEATURES_PATH)
    df["DateTime"] = pd.to_datetime(df["Date"] + " " + df["Time"])
    df = df.sort_values(by=["DateTime", "HomeTeam", "AwayTeam"]).reset_index(drop=True)
    df = df.drop(columns=["DateTime"])
    print(f"Total matches loaded: {len(df)}")

    # 2. Temporal split
    df_train = df[df["season"].isin(TRAIN_SEASONS)].copy().reset_index(drop=True)
    df_val = df[df["season"].isin(VAL_SEASONS)].copy().reset_index(drop=True)
    df_test = df[df["season"].isin(TEST_SEASONS)].copy().reset_index(drop=True)

    print(f"Train set: {len(df_train)} matches (seasons {', '.join(str(s) for s in TRAIN_SEASONS)})")
    print(f"Validation set: {len(df_val)} matches (seasons {', '.join(str(s) for s in VAL_SEASONS)})")
    print(f"Test set: {len(df_test)} matches (QUARANTINED -- not used in Epic 3)")

    # ================================================================
    # MODEL 1: Independent Double Poisson GLM
    # ================================================================
    print("\n" + "=" * 60)
    print("MODEL 1: Independent Double Poisson GLM")
    print("=" * 60)

    poisson_model = IndependentDoublePoissonGLM(
        home_feature_cols=HOME_GOAL_FEATURES,
        away_feature_cols=AWAY_GOAL_FEATURES
    )

    print("Fitting Poisson GLM on training set...")
    poisson_model.fit(df_train)

    print(f"Home model coefficients: {np.round(poisson_model.home_model.theta, 4)}")
    print(f"Away model coefficients: {np.round(poisson_model.away_model.theta, 4)}")

    # Predict on training set (in-sample)
    train_probs_poisson = poisson_model.predict_proba(df_train)
    train_brier_poisson = brier_score(train_probs_poisson, df_train["FTR"].values)
    train_logloss_poisson = log_loss(train_probs_poisson, df_train["FTR"].values)
    train_acc_poisson = accuracy(train_probs_poisson, df_train["FTR"].values)

    print(f"\n--- Poisson In-Sample (Train) ---")
    print(f"Brier Score:  {train_brier_poisson:.4f}")
    print(f"Log-Loss:     {train_logloss_poisson:.4f}")
    print(f"Accuracy:     {train_acc_poisson:.4f}")

    # Predict on validation set (out-of-sample)
    val_probs_poisson = poisson_model.predict_proba(df_val)
    val_brier_poisson = brier_score(val_probs_poisson, df_val["FTR"].values)
    val_logloss_poisson = log_loss(val_probs_poisson, df_val["FTR"].values)
    val_acc_poisson = accuracy(val_probs_poisson, df_val["FTR"].values)

    print(f"\n--- Poisson Out-of-Sample (Validation 24/25) ---")
    print(f"Brier Score:  {val_brier_poisson:.4f}")
    print(f"Log-Loss:     {val_logloss_poisson:.4f}")
    print(f"Accuracy:     {val_acc_poisson:.4f}")

    # Calibration on validation
    print("\n--- Poisson Calibration (Validation) ---")
    cal_poisson = calibration_table(val_probs_poisson, df_val["FTR"].values)
    print_calibration_table(cal_poisson)

    # ================================================================
    # MODEL 2: Dynamic Elo Ratings
    # ================================================================
    print("\n" + "=" * 60)
    print("MODEL 2: Dynamic Elo Ratings")
    print("=" * 60)

    # We need to load the processed league data (not just features) for Elo
    # because Elo processes League One too for cross-league continuity.
    champ_path = Path("data/processed/championship.csv")
    l1_path = Path("data/processed/league_one.csv")
    df_champ_raw = pd.read_csv(champ_path)
    df_l1_raw = pd.read_csv(l1_path)

    # Combine for full timeline
    df_all = pd.concat([df_champ_raw, df_l1_raw], ignore_index=True)

    # Train: fit ratings on all data up to and including season 23/24
    df_elo_train = df_all[df_all["season"].isin(TRAIN_SEASONS)].copy()

    print("Fitting Elo ratings on training timeline (Championship + League One)...")
    elo = EloTracker(K=32.0, HFA=80.0)
    elo.fit_calibration(df_elo_train)

    print(f"Calibrator fitted. Number of teams tracked: {len(elo.ratings)}")

    # Now run the full timeline including validation to get pre-match ratings for val
    # But we must NOT use val outcomes to calibrate — only to generate pre-match ratings
    df_elo_full = df_all[df_all["season"].isin(TRAIN_SEASONS + VAL_SEASONS)].copy()
    elo_full = EloTracker(K=32.0, HFA=80.0)
    elo_full.fit_timeline(df_elo_full)
    elo_full.calibrator = elo.calibrator  # Use calibrator from train only

    # Extract validation-set pre-match delta_r values
    df_elo_hist = elo_full.df_history.copy()
    # Match validation rows: Championship only, season 24/25
    df_val_champ = df_champ_raw[df_champ_raw["season"].isin(VAL_SEASONS)].copy()
    df_val_champ["DateTime"] = pd.to_datetime(df_val_champ["Date"] + " " + df_val_champ["Time"])
    df_val_champ = df_val_champ.sort_values(by=["DateTime", "HomeTeam", "AwayTeam"]).reset_index(drop=True)

    # Get delta_r for val matches from history
    # Filter history to Championship val matches
    val_delta_rs = []
    hist_idx = 0
    for _, row in df_elo_hist.iterrows():
        if row["Date"] in df_val_champ["Date"].values:
            # Check if this is a Championship match in the val set
            match = df_val_champ[
                (df_val_champ["Date"] == row["Date"]) &
                (df_val_champ["HomeTeam"] == row["HomeTeam"]) &
                (df_val_champ["AwayTeam"] == row["AwayTeam"])
            ]
            if len(match) > 0:
                val_delta_rs.append(row["delta_r"])

    val_delta_rs = np.array(val_delta_rs)

    if len(val_delta_rs) == len(df_val):
        val_probs_elo = elo_full.calibrator.predict_proba(val_delta_rs.reshape(-1, 1))

        val_brier_elo = brier_score(val_probs_elo, df_val["FTR"].values)
        val_logloss_elo = log_loss(val_probs_elo, df_val["FTR"].values)
        val_acc_elo = accuracy(val_probs_elo, df_val["FTR"].values)

        print(f"\n--- Elo Out-of-Sample (Validation 24/25) ---")
        print(f"Brier Score:  {val_brier_elo:.4f}")
        print(f"Log-Loss:     {val_logloss_elo:.4f}")
        print(f"Accuracy:     {val_acc_elo:.4f}")

        print("\n--- Elo Calibration (Validation) ---")
        cal_elo = calibration_table(val_probs_elo, df_val["FTR"].values)
        print_calibration_table(cal_elo)
    else:
        print(f"Warning: Elo validation alignment issue ({len(val_delta_rs)} delta_rs vs {len(df_val)} val matches)")
        val_brier_elo = float("nan")
        val_logloss_elo = float("nan")
        val_acc_elo = float("nan")

    # ================================================================
    # Baseline Comparison (MODEL-3)
    # ================================================================
    print("\n" + "=" * 60)
    print("BASELINE COMPARISON (Validation Set — Season 24/25)")
    print("=" * 60)

    # Naive baseline: predict league-wide average FTR distribution
    ftr_counts = df_train["FTR"].value_counts(normalize=True)
    naive_probs = np.tile([ftr_counts.get("H", 1/3), ftr_counts.get("D", 1/3), ftr_counts.get("A", 1/3)], (len(df_val), 1))
    naive_brier = brier_score(naive_probs, df_val["FTR"].values)
    naive_logloss = log_loss(naive_probs, df_val["FTR"].values)
    naive_acc = accuracy(naive_probs, df_val["FTR"].values)

    print(f"\n{'Model':<25} | {'Brier Score':>12} | {'Log-Loss':>10} | {'Accuracy':>10}")
    print("-" * 65)
    print(f"{'Naive (league avg)':<25} | {naive_brier:>12.4f} | {naive_logloss:>10.4f} | {naive_acc:>10.4f}")
    print(f"{'Poisson GLM':<25} | {val_brier_poisson:>12.4f} | {val_logloss_poisson:>10.4f} | {val_acc_poisson:>10.4f}")
    print(f"{'Elo Ratings':<25} | {val_brier_elo:>12.4f} | {val_logloss_elo:>10.4f} | {val_acc_elo:>10.4f}")

    print("\n[INFO] Test set (Season 25/26) is QUARANTINED and was not evaluated.")
    print("[INFO] Baseline training complete.")


if __name__ == "__main__":
    main()
