import pandas as pd
import numpy as np
from pathlib import Path

# Overall Prior Averages
OVERALL_PRIORS = {
    "gs": 1.35,
    "gc": 1.35,
    "pts": 1.365,
    "gd": 0.0
}

# Venue-specific Prior Averages
VENUE_PRIORS = {
    "home": {
        "gs": 1.50,
        "gc": 1.20,
        "pts": 1.60,
        "gd": 0.30
    },
    "away": {
        "gs": 1.20,
        "gc": 1.50,
        "pts": 1.13,
        "gd": -0.30
    }
}

def build_team_timelines(df_champ, df_l1):
    """
    Combines Championship and League One matches chronologically and builds a timeline
    for each team.
    Each timeline entry contains:
      - Date, Time
      - Opponent
      - Venue ('home' or 'away')
      - goals_scored, goals_conceded, points_earned, goal_difference
    """
    df = pd.concat([df_champ, df_l1], ignore_index=True)
    df["DateTime"] = pd.to_datetime(df["Date"] + " " + df["Time"])
    df = df.sort_values("DateTime").reset_index(drop=True)
    
    timelines = {}
    
    for _, row in df.iterrows():
        home = row["HomeTeam"]
        away = row["AwayTeam"]
        date_time = row["DateTime"]
        
        try:
            h_goals = int(row["FTHG"])
            a_goals = int(row["FTAG"])
        except (ValueError, TypeError):
            continue
            
        ftr = row["FTR"]
        
        # Calculate points
        h_pts = 3 if ftr == "H" else (1 if ftr == "D" else 0)
        a_pts = 3 if ftr == "A" else (1 if ftr == "D" else 0)
        
        # Home Entry
        if home not in timelines:
            timelines[home] = []
        timelines[home].append({
            "DateTime": date_time,
            "Opponent": away,
            "Venue": "home",
            "gs": h_goals,
            "gc": a_goals,
            "pts": h_pts,
            "gd": h_goals - a_goals
        })
        
        # Away Entry
        if away not in timelines:
            timelines[away] = []
        timelines[away].append({
            "DateTime": date_time,
            "Opponent": home,
            "Venue": "away",
            "gs": a_goals,
            "gc": h_goals,
            "pts": a_pts,
            "gd": a_goals - h_goals
        })
        
    for team in timelines:
        timelines[team].sort(key=lambda x: x["DateTime"])
        
    return timelines

def build_h2h_cache(df_champ, df_l1):
    """
    Builds a cache of matches played between each pair of teams, sorted chronologically.
    Key: tuple of sorted team names, e.g. ("Coventry City", "Luton Town")
    """
    df = pd.concat([df_champ, df_l1], ignore_index=True)
    df["DateTime"] = pd.to_datetime(df["Date"] + " " + df["Time"])
    df = df.sort_values("DateTime").reset_index(drop=True)
    
    h2h_cache = {}
    
    for _, row in df.iterrows():
        home = row["HomeTeam"]
        away = row["AwayTeam"]
        date_time = row["DateTime"]
        
        try:
            h_goals = int(row["FTHG"])
            a_goals = int(row["FTAG"])
        except (ValueError, TypeError):
            continue
            
        ftr = row["FTR"]
        
        key = tuple(sorted([home, away]))
        if key not in h2h_cache:
            h2h_cache[key] = []
            
        h2h_cache[key].append({
            "DateTime": date_time,
            "HomeTeam": home,
            "AwayTeam": away,
            "FTHG": h_goals,
            "FTAG": a_goals,
            "FTR": ftr
        })
        
    return h2h_cache

def get_rolling_avg(timeline, target_dt, N, key, venue_filter=None):
    """
    Computes the rolling average for a key (e.g. 'gs', 'gc', 'pts', 'gd') over the last N matches
    played strictly before target_dt.
    Optionally filters by venue ('home' or 'away').
    Applies the mathematical blending formula:
      (Sum of M matches + (N - M) * Prior Average) / N
    """
    history = [m for m in timeline if m["DateTime"] < target_dt]
    
    if venue_filter:
        history = [m for m in history if m["Venue"] == venue_filter]
        prior = VENUE_PRIORS[venue_filter][key]
    else:
        prior = OVERALL_PRIORS[key]
        
    matches = history[-N:]
    M = len(matches)
    
    if M == 0:
        return prior
        
    total_val = sum(m[key] for m in matches)
    return (total_val + (N - M) * prior) / N

def get_rest_days(timeline, target_dt):
    """
    Computes days of rest since the last match played strictly before target_dt.
    Capped at 28 days to prevent extreme pre-season/break outliers from skewing features.
    If no prior matches exist, returns 28.
    """
    history = [m for m in timeline if m["DateTime"] < target_dt]
    if not history:
        return 28
    prev_dt = history[-1]["DateTime"]
    days = (target_dt - prev_dt).days
    return max(0, min(days, 28))

def get_h2h_stats(h2h_cache, h_team, a_team, target_dt):
    """
    Computes H2H historical statistics between h_team and a_team before target_dt.
    Returns:
      - h2h_matches_played: Number of meetings
      - h2h_home_goals_avg: Average goals scored by current home team against current away team
      - h2h_away_goals_avg: Average goals scored by current away team against current home team
      - h2h_home_pts_avg: Average points earned by current home team against current away team
    If no prior meetings exist, returns None for all (which converts to empty cell).
    """
    key = tuple(sorted([h_team, a_team]))
    meetings = h2h_cache.get(key, [])
    
    # Filter strictly before target_dt
    history = [m for m in meetings if m["DateTime"] < target_dt]
    
    M = len(history)
    if M == 0:
        return None, None, None, None
        
    h_goals_sum = 0
    a_goals_sum = 0
    h_pts_sum = 0
    
    for m in history:
        prior_home = m["HomeTeam"]
        prior_away = m["AwayTeam"]
        prior_fthg = m["FTHG"]
        prior_ftag = m["FTAG"]
        prior_ftr = m["FTR"]
        
        # Determine stats from current home team's perspective
        if prior_home == h_team:
            # Current home was prior home
            h_goals_sum += prior_fthg
            a_goals_sum += prior_ftag
            h_pts_sum += 3 if prior_ftr == "H" else (1 if prior_ftr == "D" else 0)
        else:
            # Current home was prior away
            h_goals_sum += prior_ftag
            a_goals_sum += prior_fthg
            h_pts_sum += 3 if prior_ftr == "A" else (1 if prior_ftr == "D" else 0)
            
    return M, h_goals_sum / M, a_goals_sum / M, h_pts_sum / M

def generate_features(df_champ, df_l1):
    """
    Main feature generator. Iterates over df_champ and appends FEAT-1, FEAT-2, FEAT-3, and FEAT-4 features.
    """
    timelines = build_team_timelines(df_champ, df_l1)
    h2h_cache = build_h2h_cache(df_champ, df_l1)
    
    df_features = df_champ.copy()
    df_features["DateTime"] = pd.to_datetime(df_features["Date"] + " " + df_features["Time"])
    
    # Features list to generate
    features = {
        # FEAT-1: Overall rolling form
        "home_rolling_gs_5": [], "home_rolling_gs_10": [],
        "home_rolling_gc_5": [], "home_rolling_gc_10": [],
        "home_rolling_pts_5": [], "home_rolling_pts_10": [],
        "home_rolling_gd_5": [], "home_rolling_gd_10": [],
        "away_rolling_gs_5": [], "away_rolling_gs_10": [],
        "away_rolling_gc_5": [], "away_rolling_gc_10": [],
        "away_rolling_pts_5": [], "away_rolling_pts_10": [],
        "away_rolling_gd_5": [], "away_rolling_gd_10": [],
        
        # FEAT-2: Venue-specific rolling splits
        "home_venue_rolling_gs_5": [], "home_venue_rolling_gs_10": [],
        "home_venue_rolling_gc_5": [], "home_venue_rolling_gc_10": [],
        "home_venue_rolling_pts_5": [], "home_venue_rolling_pts_10": [],
        "home_venue_rolling_gd_5": [], "home_venue_rolling_gd_10": [],
        "away_venue_rolling_gs_5": [], "away_venue_rolling_gs_10": [],
        "away_venue_rolling_gs_10": [], "away_venue_rolling_gs_10": [], # typo prevention (added below)
        "away_venue_rolling_gc_5": [], "away_venue_rolling_gc_10": [],
        "away_venue_rolling_pts_5": [], "away_venue_rolling_pts_10": [],
        "away_venue_rolling_gd_5": [], "away_venue_rolling_gd_10": [],
        
        # FEAT-3: Rest days & Schedule Congestion
        "home_rest_days": [], "away_rest_days": [],
        "home_is_congested": [], "away_is_congested": [],
        
        # FEAT-4: Head-to-Head (H2H) History
        "h2h_matches_played": [],
        "h2h_home_goals_avg": [],
        "h2h_away_goals_avg": [],
        "h2h_home_pts_avg": []
    }
    # Clean up any potential duplicate keys
    if "away_venue_rolling_gs_10" in features:
        # Re-initialize to prevent duplicate mappings
        features["away_venue_rolling_gs_10"] = []
    
    for _, row in df_features.iterrows():
        home = row["HomeTeam"]
        away = row["AwayTeam"]
        dt = row["DateTime"]
        
        h_timeline = timelines.get(home, [])
        a_timeline = timelines.get(away, [])
        
        # 1. Overall Rolling Form (FEAT-1)
        features["home_rolling_gs_5"].append(get_rolling_avg(h_timeline, dt, 5, "gs"))
        features["home_rolling_gs_10"].append(get_rolling_avg(h_timeline, dt, 10, "gs"))
        features["home_rolling_gc_5"].append(get_rolling_avg(h_timeline, dt, 5, "gc"))
        features["home_rolling_gc_10"].append(get_rolling_avg(h_timeline, dt, 10, "gc"))
        features["home_rolling_pts_5"].append(get_rolling_avg(h_timeline, dt, 5, "pts"))
        features["home_rolling_pts_10"].append(get_rolling_avg(h_timeline, dt, 10, "pts"))
        features["home_rolling_gd_5"].append(get_rolling_avg(h_timeline, dt, 5, "gd"))
        features["home_rolling_gd_10"].append(get_rolling_avg(h_timeline, dt, 10, "gd"))
        
        features["away_rolling_gs_5"].append(get_rolling_avg(a_timeline, dt, 5, "gs"))
        features["away_rolling_gs_10"].append(get_rolling_avg(a_timeline, dt, 10, "gs"))
        features["away_rolling_gc_5"].append(get_rolling_avg(a_timeline, dt, 5, "gc"))
        features["away_rolling_gc_10"].append(get_rolling_avg(a_timeline, dt, 10, "gc"))
        features["away_rolling_pts_5"].append(get_rolling_avg(a_timeline, dt, 5, "pts"))
        features["away_rolling_pts_10"].append(get_rolling_avg(a_timeline, dt, 10, "pts"))
        features["away_rolling_gd_5"].append(get_rolling_avg(a_timeline, dt, 5, "gd"))
        features["away_rolling_gd_10"].append(get_rolling_avg(a_timeline, dt, 10, "gd"))
        
        # 2. Venue-specific Rolling splits (FEAT-2)
        features["home_venue_rolling_gs_5"].append(get_rolling_avg(h_timeline, dt, 5, "gs", "home"))
        features["home_venue_rolling_gs_10"].append(get_rolling_avg(h_timeline, dt, 10, "gs", "home"))
        features["home_venue_rolling_gc_5"].append(get_rolling_avg(h_timeline, dt, 5, "gc", "home"))
        features["home_venue_rolling_gc_10"].append(get_rolling_avg(h_timeline, dt, 10, "gc", "home"))
        features["home_venue_rolling_pts_5"].append(get_rolling_avg(h_timeline, dt, 5, "pts", "home"))
        features["home_venue_rolling_pts_10"].append(get_rolling_avg(h_timeline, dt, 10, "pts", "home"))
        features["home_venue_rolling_gd_5"].append(get_rolling_avg(h_timeline, dt, 5, "gd", "home"))
        features["home_venue_rolling_gd_10"].append(get_rolling_avg(h_timeline, dt, 10, "gd", "home"))
        
        features["away_venue_rolling_gs_5"].append(get_rolling_avg(a_timeline, dt, 5, "gs", "away"))
        features["away_venue_rolling_gs_10"].append(get_rolling_avg(a_timeline, dt, 10, "gs", "away"))
        features["away_venue_rolling_gc_5"].append(get_rolling_avg(a_timeline, dt, 5, "gc", "away"))
        features["away_venue_rolling_gc_10"].append(get_rolling_avg(a_timeline, dt, 10, "gc", "away"))
        features["away_venue_rolling_pts_5"].append(get_rolling_avg(a_timeline, dt, 5, "pts", "away"))
        features["away_venue_rolling_pts_10"].append(get_rolling_avg(a_timeline, dt, 10, "pts", "away"))
        features["away_venue_rolling_gd_5"].append(get_rolling_avg(a_timeline, dt, 5, "gd", "away"))
        features["away_venue_rolling_gd_10"].append(get_rolling_avg(a_timeline, dt, 10, "gd", "away"))
        
        # 3. Rest Days & Schedule Congestion (FEAT-3)
        h_rest = get_rest_days(h_timeline, dt)
        a_rest = get_rest_days(a_timeline, dt)
        features["home_rest_days"].append(h_rest)
        features["away_rest_days"].append(a_rest)
        features["home_is_congested"].append(1 if h_rest <= 4 else 0)
        features["away_is_congested"].append(1 if a_rest <= 4 else 0)
        
        # 4. H2H Stats (FEAT-4)
        m_played, h_avg_g, a_avg_g, h_avg_pts = get_h2h_stats(h2h_cache, home, away, dt)
        features["h2h_matches_played"].append(m_played if m_played is not None else "")
        features["h2h_home_goals_avg"].append(h_avg_g if h_avg_g is not None else "")
        features["h2h_away_goals_avg"].append(a_avg_g if a_avg_g is not None else "")
        features["h2h_home_pts_avg"].append(h_avg_pts if h_avg_pts is not None else "")
        
    # Append to DataFrame
    for feat_name, values in features.items():
        df_features[feat_name] = values
        
    df_features = df_features.drop(columns=["DateTime"])
    return df_features
