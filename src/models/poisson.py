import numpy as np
import scipy.optimize as opt
from scipy.stats import poisson

class PoissonModel:
    """
    Fits a single Poisson regression model using MLE with a log-link function.
    Target goals: lambda_i = exp(X_i * theta)
    """
    def __init__(self):
        self.theta = None
        
    def _neg_log_likelihood(self, theta, X, y):
        # Prevent overflow by clipping large dot products
        linear_predictor = np.clip(np.dot(X, theta), -20, 20)
        expected_goals = np.exp(linear_predictor)
        # NLL = - sum( y * log_lambda - lambda )
        nll = -np.sum(y * linear_predictor - expected_goals)
        return nll

    def fit(self, X, y):
        # X: numpy array of shape (N, P) where first column is 1s (intercept)
        # y: numpy array of shape (N,)
        N, P = X.shape
        # Initialize theta to zeros
        initial_theta = np.zeros(P)
        
        # Optimize using L-BFGS-B
        res = opt.minimize(
            self._neg_log_likelihood,
            initial_theta,
            args=(X, y),
            method="L-BFGS-B"
        )
        
        if not res.success:
            print(f"Warning: Poisson optimization did not converge: {res.message}")
            
        self.theta = res.x
        return self

    def predict_expected(self, X):
        # Calculate expected goals
        linear_predictor = np.clip(np.dot(X, self.theta), -20, 20)
        return np.exp(linear_predictor)


class IndependentDoublePoissonGLM:
    """
    Integrates two PoissonModel instances to predict home goals and away goals,
    then combines them using joint probabilities to output 1X2 market probabilities.
    """
    def __init__(self, home_feature_cols, away_feature_cols):
        self.home_feature_cols = home_feature_cols
        self.away_feature_cols = away_feature_cols
        self.home_model = PoissonModel()
        self.away_model = PoissonModel()

    def fit(self, df):
        """
        Fits the home and away goal models using the specified columns.
        """
        # Prepare design matrices
        # We add a constant column of 1s for the intercept
        X_home = np.column_stack([np.ones(len(df)), df[self.home_feature_cols].values])
        y_home = df["FTHG"].values.astype(float)
        
        X_away = np.column_stack([np.ones(len(df)), df[self.away_feature_cols].values])
        y_away = df["FTAG"].values.astype(float)
        
        self.home_model.fit(X_home, y_home)
        self.away_model.fit(X_away, y_away)
        return self

    def predict_lambdas(self, df):
        """
        Predicts expected goals (lambda_home, mu_away) for each match.
        """
        X_home = np.column_stack([np.ones(len(df)), df[self.home_feature_cols].values])
        X_away = np.column_stack([np.ones(len(df)), df[self.away_feature_cols].values])
        
        lambdas = self.home_model.predict_expected(X_home)
        mus = self.away_model.predict_expected(X_away)
        return lambdas, mus

    def predict_proba(self, df, max_goals=15):
        """
        Predicts 1X2 probabilities for each match.
        Returns:
          - probabilities: numpy array of shape (N, 3) where columns are (Home Win, Draw, Away Win)
        """
        lambdas, mus = self.predict_lambdas(df)
        N = len(df)
        probs = np.zeros((N, 3))
        
        # Precompute poisson probabilities up to max_goals
        # goals_grid shape: (max_goals + 1,)
        goals = np.arange(max_goals + 1)
        
        for i in range(N):
            lam = lambdas[i]
            mu = mus[i]
            
            # Probability mass functions
            p_home = poisson.pmf(goals, lam)
            p_away = poisson.pmf(goals, mu)
            
            # Construct joint probability grid (outer product)
            # grid[i, j] = P(home scores i) * P(away scores j)
            grid = np.outer(p_home, p_away)
            
            # Sum grid segments
            # Home Win: i > j  (lower triangle)
            p_win = np.sum(np.tril(grid, k=-1))
            # Draw: i == j  (diagonal)
            p_draw = np.sum(np.diag(grid))
            # Away Win: i < j  (upper triangle)
            p_loss = np.sum(np.triu(grid, k=1))
            
            # Normalize to ensure they sum exactly to 1.0 (correcting for truncation)
            total = p_win + p_draw + p_loss
            if total > 0:
                p_win /= total
                p_draw /= total
                p_loss /= total
            else:
                p_win, p_draw, p_loss = 1/3, 1/3, 1/3
                
            probs[i] = [p_win, p_draw, p_loss]
            
        return probs
