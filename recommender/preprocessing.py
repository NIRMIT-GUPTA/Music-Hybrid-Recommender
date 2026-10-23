from pathlib import Path
import pandas as pd

REQUIRED = ["track_id", "track_name", "artists", "popularity", "duration_ms", "track_genre"]
NUMERIC = ["danceability", "energy", "loudness", "speechiness", "acousticness", "instrumentalness", "liveness", "valence", "tempo", "duration_ms", "time_signature"]

def clean_dataset(source, destination=None):
    """Clean Spotify metadata while retaining one useful row per track ID."""
    df = pd.read_csv(source, low_memory=False)
    df = df.loc[:, ~df.columns.astype(str).str.match(r"^Unnamed")]
    missing = set(REQUIRED) - set(df.columns)
    if missing: raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")
    for col in NUMERIC:
        if col not in df: df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].median() if df[col].notna().any() else 0.0)
    for col in ["track_id", "track_name", "artists", "album_name", "track_genre"]:
        if col in df: df[col] = df[col].fillna("Unknown").astype(str).str.strip()
    df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce").fillna(0).clip(0, 100)
    df = df[(df.track_id != "") & (df.track_name != "")]
    df = df.sort_values("popularity", ascending=False).drop_duplicates("track_id").drop_duplicates(subset=["track_name"]).reset_index(drop=True)
    if destination:
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(destination, index=False)
    return df

def load_processed(path):
    return pd.read_parquet(path)
