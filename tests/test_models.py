import unittest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.models.poisson import PoissonModel, IndependentDoublePoissonGLM
from src.models.elo import EloTracker
from src.models.evaluate import brier_score, log_loss, accuracy


class TestPoissonModel(unittest.TestCase):

    def test_predict_proba_sums_to_one(self):
        """Predicted 1X2 probabilities must sum to 1.0 for every match."""
        df = pd.DataFrame([
            {"HomeTeam": "A", "AwayTeam": "B", "FTHG": 2, "FTAG": 1, "FTR": "H",
             "f1": 1.5, "f2": 1.2, "f3": 1.3, "f4": 1.1},
            {"HomeTeam": "C", "AwayTeam": "D", "FTHG": 0, "FTAG": 0, "FTR": "D",
             "f1": 1.0, "f2": 1.0, "f3": 1.0, "f4": 1.0},
            {"HomeTeam": "A", "AwayTeam": "C", "FTHG": 1, "FTAG": 3, "FTR": "A",
             "f1": 1.2, "f2": 1.8, "f3": 0.8, "f4": 1.6},
        ])
        model = IndependentDoublePoissonGLM(
            home_feature_cols=["f1", "f2"],
            away_feature_cols=["f3", "f4"]
        )
        model.fit(df)
        probs = model.predict_proba(df)

        for i in range(len(df)):
            self.assertAlmostEqual(np.sum(probs[i]), 1.0, places=5,
                                   msg=f"Row {i} probabilities do not sum to 1.0")

    def test_log_link_positive_lambdas(self):
        """Expected goals from the log-link must always be strictly positive."""
        df = pd.DataFrame([
            {"HomeTeam": "A", "AwayTeam": "B", "FTHG": 0, "FTAG": 0, "FTR": "D",
             "f1": -5.0, "f2": -5.0, "f3": -5.0, "f4": -5.0},
            {"HomeTeam": "C", "AwayTeam": "D", "FTHG": 5, "FTAG": 5, "FTR": "D",
             "f1": 5.0, "f2": 5.0, "f3": 5.0, "f4": 5.0},
        ])
        model = IndependentDoublePoissonGLM(
            home_feature_cols=["f1", "f2"],
            away_feature_cols=["f3", "f4"]
        )
        model.fit(df)
        lambdas, mus = model.predict_lambdas(df)

        for i in range(len(df)):
            self.assertGreater(lambdas[i], 0.0, f"Lambda must be > 0 at row {i}")
            self.assertGreater(mus[i], 0.0, f"Mu must be > 0 at row {i}")


class TestEloTracker(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame([
            {"Date": "2021-08-01", "Time": "15:00", "HomeTeam": "A", "AwayTeam": "B",
             "FTHG": 2, "FTAG": 1, "FTR": "H", "season": "2122"},
            {"Date": "2021-08-08", "Time": "15:00", "HomeTeam": "B", "AwayTeam": "C",
             "FTHG": 0, "FTAG": 3, "FTR": "A", "season": "2122"},
            {"Date": "2021-08-15", "Time": "15:00", "HomeTeam": "C", "AwayTeam": "A",
             "FTHG": 1, "FTAG": 1, "FTR": "D", "season": "2122"},
        ])

    def test_chronological_update(self):
        """Elo ratings must update in strict chronological order."""
        elo = EloTracker(K=32.0, HFA=80.0)
        elo.fit_timeline(self.df)

        # After match 1 (A beats B 2-1), A should be higher than 1500, B lower
        # Initial: both 1500. A wins at home.
        self.assertGreater(elo.ratings["A"], 1500.0)
        self.assertLess(elo.ratings["B"], 1500.0)

    def test_margin_of_victory_scaling(self):
        """A large margin win should cause a bigger rating change than a narrow win."""
        df_narrow = pd.DataFrame([
            {"Date": "2021-08-01", "Time": "15:00", "HomeTeam": "X", "AwayTeam": "Y",
             "FTHG": 1, "FTAG": 0, "FTR": "H", "season": "2122"},
        ])
        df_blowout = pd.DataFrame([
            {"Date": "2021-08-01", "Time": "15:00", "HomeTeam": "X", "AwayTeam": "Y",
             "FTHG": 5, "FTAG": 0, "FTR": "H", "season": "2122"},
        ])

        elo_narrow = EloTracker(K=32.0, HFA=80.0)
        elo_narrow.fit_timeline(df_narrow)
        narrow_change = abs(elo_narrow.ratings["X"] - 1500.0)

        elo_blowout = EloTracker(K=32.0, HFA=80.0)
        elo_blowout.fit_timeline(df_blowout)
        blowout_change = abs(elo_blowout.ratings["X"] - 1500.0)

        self.assertGreater(blowout_change, narrow_change,
                           "5-0 win should produce a larger rating change than 1-0")


class TestEvaluationMetrics(unittest.TestCase):

    def test_brier_perfect(self):
        """Perfect predictions should yield Brier Score = 0."""
        probs = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
        actuals = ["H", "D", "A"]
        self.assertAlmostEqual(brier_score(probs, actuals), 0.0, places=5)

    def test_brier_uniform(self):
        """Uniform (1/3, 1/3, 1/3) predictions should yield Brier Score = 2/3."""
        probs = np.tile([1/3, 1/3, 1/3], (100, 1))
        actuals = ["H"] * 34 + ["D"] * 33 + ["A"] * 33
        bs = brier_score(probs, actuals)
        self.assertAlmostEqual(bs, 2/3, places=2)

    def test_logloss_perfect(self):
        """Near-perfect predictions should yield near-zero log-loss."""
        probs = np.array([[0.999, 0.0005, 0.0005], [0.0005, 0.999, 0.0005]])
        actuals = ["H", "D"]
        ll = log_loss(probs, actuals)
        self.assertLess(ll, 0.01)

    def test_accuracy_correct(self):
        """All correct predictions should yield accuracy = 1.0."""
        probs = np.array([[0.7, 0.2, 0.1], [0.1, 0.8, 0.1], [0.1, 0.2, 0.7]])
        actuals = ["H", "D", "A"]
        self.assertAlmostEqual(accuracy(probs, actuals), 1.0)


if __name__ == "__main__":
    unittest.main()
