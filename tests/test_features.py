import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add root folder to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.features import generate_features, build_team_timelines, get_rolling_avg, get_rest_days, get_h2h_stats

class TestFeatures(unittest.TestCase):
    
    def setUp(self):
        # Create a simple mock dataset of matches
        self.df_mock_champ = pd.DataFrame([
            # Season 2122
            {"Div": "E1", "Date": "2021-08-01", "Time": "15:00", "HomeTeam": "Team A", "AwayTeam": "Team B", "FTHG": "2", "FTAG": "1", "FTR": "H", "season": "2122", "clv_reference_book": "pinnacle"},
            {"Div": "E1", "Date": "2021-08-08", "Time": "15:00", "HomeTeam": "Team B", "AwayTeam": "Team C", "FTHG": "0", "FTAG": "3", "FTR": "A", "season": "2122", "clv_reference_book": "pinnacle"},
            {"Div": "E1", "Date": "2021-08-15", "Time": "15:00", "HomeTeam": "Team C", "AwayTeam": "Team A", "FTHG": "1", "FTAG": "1", "FTR": "D", "season": "2122", "clv_reference_book": "pinnacle"},
            {"Div": "E1", "Date": "2021-08-22", "Time": "15:00", "HomeTeam": "Team A", "AwayTeam": "Team D", "FTHG": "3", "FTAG": "0", "FTR": "H", "season": "2122", "clv_reference_book": "pinnacle"},
        ])
        
        # Mock League One
        self.df_mock_l1 = pd.DataFrame([
            {"Div": "E2", "Date": "2021-08-01", "Time": "15:00", "HomeTeam": "Team C", "AwayTeam": "Team D", "FTHG": "1", "FTAG": "0", "FTR": "H", "season": "2122", "clv_reference_book": "pinnacle"},
        ])

    def test_shift_logic_no_leakage(self):
        """
        Verify that features for Match N only reflect matches 0 to N-1 (no leakage of current match result).
        """
        df_feat = generate_features(self.df_mock_champ, self.df_mock_l1)
        
        row0 = df_feat.iloc[0]
        self.assertEqual(row0["home_rolling_gs_5"], 1.35)
        self.assertEqual(row0["away_rolling_gs_5"], 1.35)
        
        row1 = df_feat.iloc[1]
        self.assertAlmostEqual(row1["home_rolling_gs_5"], 1.28) # Team B is HomeTeam here

    def test_relegation_cold_start_imputation(self):
        """
        Verify the mathematical blending formula for teams with fewer than N matches:
        (Sum of M matches + (N - M) * Prior Average) / N
        """
        df_feat = generate_features(self.df_mock_champ, self.df_mock_l1)
        row3 = df_feat.iloc[3]
        
        # Team D is AwayTeam in Match 3
        # D played 1 match in E2: scored 0, conceded 1, 0 points
        self.assertAlmostEqual(row3["away_rolling_gs_5"], 1.08) # (0 + 4*1.35)/5 = 1.08
        self.assertAlmostEqual(row3["away_rolling_gc_5"], 1.28) # (1 + 4*1.35)/5 = 1.28
        self.assertAlmostEqual(row3["away_rolling_pts_5"], 1.092) # (0 + 4*1.365)/5 = 1.092
        self.assertAlmostEqual(row3["away_rolling_gd_5"], -0.2) # (-1 + 4*0)/5 = -0.2

    def test_rest_days(self):
        """
        Verify that rest days calculations are correct and bounded.
        """
        df_feat = generate_features(self.df_mock_champ, self.df_mock_l1)
        
        # Match 0: Team A vs Team B on 2021-08-01. Neither has prior history.
        row0 = df_feat.iloc[0]
        self.assertEqual(row0["home_rest_days"], 28)
        self.assertEqual(row0["away_rest_days"], 28)
        
        # Match 2: Team C vs Team A on 2021-08-15.
        # Team A's last match: 2021-08-01. Rest = 14 days.
        # Team C's last match: 2021-08-08. Rest = 7 days.
        row2 = df_feat.iloc[2]
        self.assertEqual(row2["home_rest_days"], 7) # Team C is HomeTeam
        self.assertEqual(row2["away_rest_days"], 14) # Team A is AwayTeam
        self.assertEqual(row2["home_is_congested"], 0)
        self.assertEqual(row2["away_is_congested"], 0)

    def test_h2h_history(self):
        """
        Verify that H2H statistics are correctly calculated and empty/nan for first-ever meetings.
        """
        df_feat = generate_features(self.df_mock_champ, self.df_mock_l1)
        
        # Match 0: Team A vs Team B on 2021-08-01. First meeting.
        row0 = df_feat.iloc[0]
        self.assertTrue(pd.isna(row0["h2h_matches_played"]) or row0["h2h_matches_played"] == "")
        
        # Let's verify with a manual check on a second meeting.
        # Let's create a custom H2H test case.
        h2h_cache = {
            ("Team A", "Team B"): [
                {"DateTime": pd.to_datetime("2021-08-01 15:00:00"), "HomeTeam": "Team A", "AwayTeam": "Team B", "FTHG": 2, "FTAG": 1, "FTR": "H"}
            ]
        }
        # Check H2H stats for a meeting on 2021-08-10.
        # From perspective of Team B (Home) vs Team A (Away)
        m_played, h_avg_g, a_avg_g, h_avg_pts = get_h2h_stats(h2h_cache, "Team B", "Team A", pd.to_datetime("2021-08-10 15:00:00"))
        
        self.assertEqual(m_played, 1)
        # Team B scored 1 in prior match (since it was AwayTeam and FTAG=1)
        self.assertEqual(h_avg_g, 1.0)
        # Team A scored 2 in prior match (HomeTeam and FTHG=2)
        self.assertEqual(a_avg_g, 2.0)
        # Team B got 0 points (since Team A won)
        self.assertEqual(h_avg_pts, 0.0)

    def test_venue_performance_splits(self):
        """
        Verify that home stats are systematically stronger than away stats league-wide on actual Championship data.
        """
        features_path = Path("data/features/championship_features.csv")
        if not features_path.exists():
            print("Skipping league-wide venue performance check as dataset is not generated yet.")
            return
            
        df = pd.read_csv(features_path)
        
        mean_home_pts_5 = df["home_venue_rolling_pts_5"].mean()
        mean_away_pts_5 = df["away_venue_rolling_pts_5"].mean()
        
        print(f"\n--- FEAT-2 Venue Splits Sanity Check ---")
        print(f"League-wide Mean Home-Only Rolling Points (N=5): {mean_home_pts_5:.3f}")
        print(f"League-wide Mean Away-Only Rolling Points (N=5): {mean_away_pts_5:.3f}")
        
        self.assertGreater(mean_home_pts_5, mean_away_pts_5)
        
        mean_home_gs_5 = df["home_venue_rolling_gs_5"].mean()
        mean_away_gs_5 = df["away_venue_rolling_gs_5"].mean()
        self.assertGreater(mean_home_gs_5, mean_away_gs_5)

if __name__ == "__main__":
    unittest.main()
