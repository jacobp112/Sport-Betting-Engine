import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

class EloTracker:
    """
    Tracks dynamic team Elo ratings chronologically.
    Supports K-factor margin-of-victory scaling and HFA.
    """
    def __init__(self, K=32.0, HFA=80.0):
        self.K = K
        self.HFA = HFA
        self.ratings = {}  # team -> current rating
        self.rating_history = []  # List of dicts with match index and pre-match ratings
        
        # Multinomial Logistic Regression to map Delta R -> 1X2 probabilities
        self.calibrator = None

    def get_rating(self, team):
        # Initialize to 1500 if not seen
        if team not in self.ratings:
            self.ratings[team] = 1500.0
        return self.ratings[team]

    def fit_timeline(self, df):
        """
        Processes matches chronologically and updates ratings.
        Saves the pre-match ratings for feature engineering.
        """
        # Ensure chronological order
        df_sorted = df.copy()
        df_sorted["DateTime"] = pd.to_datetime(df_sorted["Date"] + " " + df_sorted["Time"])
        df_sorted = df_sorted.sort_values("DateTime").reset_index(drop=True)
        
        self.rating_history = []
        
        for idx, row in df_sorted.iterrows():
            home = row["HomeTeam"]
            away = row["AwayTeam"]
            
            # 1. Fetch pre-match ratings
            r_h = self.get_rating(home)
            r_a = self.get_rating(away)
            
            # Save history
            self.rating_history.append({
                "Date": row["Date"],
                "HomeTeam": home,
                "AwayTeam": away,
                "home_pre_rating": r_h,
                "away_pre_rating": r_a,
                "delta_r": r_h + self.HFA - r_a
            })
            
            # 2. Skip update if goals or FTR are missing (postponed / incomplete)
            try:
                h_goals = int(row["FTHG"])
                a_goals = int(row["FTAG"])
            except (ValueError, TypeError):
                continue
                
            ftr = row["FTR"]
            if ftr not in ["H", "D", "A"]:
                continue
                
            # 3. Elo Calculations
            dr = r_h + self.HFA - r_a
            w_h = 1.0 / (10.0 ** (-dr / 400.0) + 1.0)
            
            # Actual score from Home perspective
            s_h = 1.0 if ftr == "H" else (0.5 if ftr == "D" else 0.0)
            
            # Margin of victory scaling (FIFA standard)
            diff = abs(h_goals - a_goals)
            if diff <= 1:
                mult = 1.0
            elif diff == 2:
                mult = 1.5
            elif diff == 3:
                mult = 1.75
            else:
                mult = 1.75 + (diff - 3.0) / 8.0
                
            # Update ratings
            change = self.K * mult * (s_h - w_h)
            self.ratings[home] = r_h + change
            self.ratings[away] = r_a - change
            
        # Convert history to DataFrame
        self.df_history = pd.DataFrame(self.rating_history)
        return self

    def fit_calibration(self, df_train):
        """
        Fits a multinomial logistic regression calibrator to map rating difference
        (home_pre_rating + HFA - away_pre_rating) -> FTR.
        """
        # Align training df with our chronological pre-match ratings
        df_train_sorted = df_train.copy()
        df_train_sorted["DateTime"] = pd.to_datetime(df_train_sorted["Date"] + " " + df_train_sorted["Time"])
        df_train_sorted = df_train_sorted.sort_values("DateTime").reset_index(drop=True)
        
        # Construct timelines and extract pre-match ratings
        self.ratings = {} # reset ratings to fit training set from scratch
        self.fit_timeline(df_train_sorted)
        
        # Merge pre-match ratings with FTR target
        X = self.df_history["delta_r"].values.reshape(-1, 1)
        
        # Map FTR: H=0, D=1, A=2 to keep class mapping deterministic
        y_map = {"H": 0, "D": 1, "A": 2}
        y = df_train_sorted["FTR"].map(y_map).values
        
        # Fit logistic regression
        self.calibrator = LogisticRegression(C=1e5, max_iter=1000)
        self.calibrator.fit(X, y)
        return self

    def predict_proba(self, delta_rs):
        """
        Predicts 1X2 probabilities for a list of rating differences (delta_r).
        Returns:
          - probabilities: numpy array of shape (len(delta_rs), 3) representing (Home Win, Draw, Away Win)
        """
        if self.calibrator is None:
            raise ValueError("Calibrator is not fit! Call fit_calibration first.")
            
        X = np.array(delta_rs).reshape(-1, 1)
        probs = self.calibrator.predict_proba(X)
        
        # Return in order (Home Win [0], Draw [1], Away Win [2])
        return probs
