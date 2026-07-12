import numpy as np


def brier_score(probs, actuals):
    """
    Computes the multi-class Brier Score.
    probs: numpy array of shape (N, 3) with columns (P_Home, P_Draw, P_Away).
    actuals: array-like of FTR strings ("H", "D", "A").
    
    Brier Score = (1/N) * sum_i sum_k (p_ik - o_ik)^2
    where o_ik is 1 if outcome k occurred, else 0.
    Lower is better. Perfect = 0.0, uninformative (1/3, 1/3, 1/3) = 0.667.
    """
    ftr_map = {"H": 0, "D": 1, "A": 2}
    N = len(actuals)
    one_hot = np.zeros((N, 3))
    for i, ftr in enumerate(actuals):
        one_hot[i, ftr_map[ftr]] = 1.0

    return np.mean(np.sum((probs - one_hot) ** 2, axis=1))


def log_loss(probs, actuals, eps=1e-15):
    """
    Computes the multi-class Log-Loss (cross-entropy).
    probs: numpy array of shape (N, 3) with columns (P_Home, P_Draw, P_Away).
    actuals: array-like of FTR strings ("H", "D", "A").

    Log-Loss = -(1/N) * sum_i sum_k o_ik * log(p_ik)
    Lower is better. Perfect = 0.0, uninformative (1/3, 1/3, 1/3) = 1.099.
    """
    ftr_map = {"H": 0, "D": 1, "A": 2}
    N = len(actuals)
    one_hot = np.zeros((N, 3))
    for i, ftr in enumerate(actuals):
        one_hot[i, ftr_map[ftr]] = 1.0

    # Clip to prevent log(0)
    clipped = np.clip(probs, eps, 1.0 - eps)
    return -np.mean(np.sum(one_hot * np.log(clipped), axis=1))


def accuracy(probs, actuals):
    """
    Computes classification accuracy (predicted class vs actual).
    """
    ftr_map = {"H": 0, "D": 1, "A": 2}
    predicted = np.argmax(probs, axis=1)
    actual_idx = np.array([ftr_map[ftr] for ftr in actuals])
    return np.mean(predicted == actual_idx)


def calibration_table(probs, actuals, n_bins=10):
    """
    Builds a calibration table for each outcome class (Home Win, Draw, Away Win).
    Returns a list of dicts, one per bin, containing:
      - bin_lower, bin_upper: probability range
      - predicted_mean: mean predicted probability in this bin
      - actual_freq: actual frequency of the outcome in this bin
      - count: number of predictions in this bin
    """
    ftr_map = {"H": 0, "D": 1, "A": 2}
    labels = ["Home Win", "Draw", "Away Win"]
    N = len(actuals)
    one_hot = np.zeros((N, 3))
    for i, ftr in enumerate(actuals):
        one_hot[i, ftr_map[ftr]] = 1.0

    tables = {}
    for cls_idx, label in enumerate(labels):
        cls_probs = probs[:, cls_idx]
        cls_actual = one_hot[:, cls_idx]
        bins = np.linspace(0, 1, n_bins + 1)
        table = []
        for b in range(n_bins):
            lo, hi = bins[b], bins[b + 1]
            mask = (cls_probs >= lo) & (cls_probs < hi)
            if b == n_bins - 1:
                mask = (cls_probs >= lo) & (cls_probs <= hi)
            count = int(np.sum(mask))
            if count > 0:
                pred_mean = float(np.mean(cls_probs[mask]))
                actual_freq = float(np.mean(cls_actual[mask]))
            else:
                pred_mean = (lo + hi) / 2
                actual_freq = 0.0
            table.append({
                "bin_lower": round(lo, 3),
                "bin_upper": round(hi, 3),
                "predicted_mean": round(pred_mean, 4),
                "actual_freq": round(actual_freq, 4),
                "count": count
            })
        tables[label] = table
    return tables


def print_calibration_table(tables):
    """Pretty-prints calibration tables."""
    for label, rows in tables.items():
        print(f"\n--- Calibration: {label} ---")
        print(f"{'Bin':>12} | {'Pred Mean':>10} | {'Actual Freq':>12} | {'Count':>6}")
        print("-" * 50)
        for r in rows:
            bin_str = f"{r['bin_lower']:.2f}-{r['bin_upper']:.2f}"
            print(f"{bin_str:>12} | {r['predicted_mean']:>10.4f} | {r['actual_freq']:>12.4f} | {r['count']:>6}")
