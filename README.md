# Hybrid Music Recommendation System

A music recommendation system that returns the top 10 tracks from one
input: a selected song or a selected genre. It combines content-based
similarity with item-item collaborative filtering and presents
recommendations through a Streamlit interface and a Django web
application.

## Overview

The system uses two recommendation engines:

-   **Content-based filtering** compares track metadata, genre, artist,
    and audio features.

-   **Item-item collaborative filtering** scores tracks using a sparse
    matrix of synthetic user--track interactions.

-   **Hybrid ranking** combines the normalized scores from both engines:

    \\[ `\\text{Hybrid Score}`{=tex} =
    `\\alpha `{=tex}`\\times `{=tex}`\\text{Normalized Content Score}`{=tex} +
    (1-`\\alpha`{=tex})
    `\\times `{=tex}`\\text{Normalized Collaborative Score}`{=tex} \\]

The current hybrid recommender uses `alpha=0.5` by default. The
optimization script tests alpha values from `0.0` to `1.0` in increments
of `0.1` and selects the value with the highest average NDCG@10 on its
validation examples.

## Data

The project uses a Spotify track metadata dataset obtained from Kaggle.
The supplied metadata does not contain real listener interactions.

The preprocessing pipeline cleans the dataset, checks required columns,
converts numeric features, handles missing values, constrains popularity
to the range 0--100, and removes duplicate track IDs and track names.
The cleaned catalog is saved in Parquet format.

Content features include:

-   Track genre and artist
-   Danceability, energy, loudness, speechiness, acousticness,
    instrumentalness, liveness, and valence
-   Tempo, duration, and time signature

Because real listening histories are unavailable,
`generate_demo_interactions.py` creates reproducible, genre-biased
**synthetic** interaction events. These interactions are used to
demonstrate and evaluate collaborative filtering; they are not real
Spotify listener behavior.

## Architecture

``` text
Kaggle track metadata (CSV)
          |
          v
   Data preprocessing
          |
          v
Processed track catalog (Parquet)
          |
          +------------------------------+
          |                              |
          v                              v
 Content-based engine          Synthetic interactions
          |                              |
          |                              v
          |                  Sparse item-item CF engine
          |                              |
          +---------------+--------------+
                          |
                          v
                 Normalize and combine
                    content + CF scores
                          |
              +-----------+-----------+
              |                       |
              v                       v
   Streamlit top-10 results   Django web application
                              (search, recommend,
                               favourites, history,
                               user accounts)
```

The application supports two recommendation modes:

1.  **Recommend by Song** --- select a track and recommend similar
    tracks. The selected seed track is excluded from the results.
2.  **Recommend by Genre** --- select a genre and recommend tracks from
    that genre.

Missing collaborative scores are treated as zero before candidate-set
min-max normalization. In genre mode, candidates remain within the
selected genre.

## Project Structure

``` text
Music-Hybrid-Recommender/
├── data/
│   ├── raw/
│   │   └── dataset.csv
│   ├── processed/
│   │   └── tracks.parquet          (generated)
│   └── interactions/
│       └── synthetic_interactions.npz (generated)
├── models/
│   ├── content.joblib              (generated)
│   └── collaborative.joblib        (generated)
├── recommender/
│   ├── __init__.py
│   ├── preprocessing.py
│   ├── content_based.py
│   ├── collaborative.py
│   ├── hybrid.py
│   └── evaluation.py
├── scripts/
│   ├── prepare_data.py
│   ├── generate_demo_interactions.py
│   ├── train_models.py
│   ├── optimize_hybrid.py
│   └── evaluate_models.py
├── config/                         (Django project settings)
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── musicapp/                       (Django app)
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── engine.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/
│   │   ├── __init__.py
│   │   ├── 0001_initial.py
│   │   └── 0002_user_profiles.py
│   ├── static/musicapp/
│   │   ├── css/style.css
│   │   └── js/app.js
│   └── templates/
│       ├── base.html
│       ├── musicapp/index.html
│       └── registration/
│           ├── login.html
│           └── signup.html
├── manage.py
├── streamlit_app.py
├── requirements.txt
├── README.md
```

Generated files appear after running the relevant scripts. The `models/`
directory is created by the training script as needed.

## Core Modules

### `recommender/preprocessing.py`

Cleans the source CSV, validates required columns, converts and fills
numeric features, cleans text fields, removes invalid rows and
duplicates, and optionally saves the processed catalog. It also provides
a function to load the processed Parquet file.

### `recommender/content_based.py`

Builds a content feature representation using scaled numeric features,
one-hot encoded genre, and TF-IDF artist features. It uses cosine
similarity and nearest neighbours to score tracks by similarity to a
selected song.

### `recommender/collaborative.py`

Creates a sparse item-item interaction matrix and computes item-item
cosine-style scores from synthetic interactions. It also simulates
reproducible, genre-biased interactions for demonstration purposes.

### `recommender/hybrid.py`

Combines content and collaborative scores after min-max normalization.
It supports song-based and genre-based recommendations and returns
ranked results with component scores.

### `recommender/evaluation.py`

Implements ranking metrics including Precision@K, Recall@K, MAP@K,
NDCG@K, catalogue coverage, and recommendation diversity.

## Scripts

  -------------------------------------------------------------------------------------------
  Script                                    Purpose
  ----------------------------------------- -------------------------------------------------
  `scripts/prepare_data.py`                 Cleans `data/raw/dataset.csv` and writes
                                            `data/processed/tracks.parquet`.

  `scripts/generate_demo_interactions.py`   Generates synthetic interactions and saves
                                            `data/interactions/synthetic_interactions.npz`.

  `scripts/train_models.py`                 Builds the content and collaborative engines and
                                            saves them as Joblib artifacts in `models/`.

  `scripts/optimize_hybrid.py`              Tests alpha values from 0.0 to 1.0 and chooses
                                            the value with the best average NDCG@10 on
                                            held-out synthetic interactions.

  `scripts/evaluate_models.py`              Compares content, collaborative, hybrid, and
                                            popularity-baseline recommendations using
                                            held-out synthetic interactions; saves metrics
                                            and a chart.
  -------------------------------------------------------------------------------------------

## Setup and Run

The commands below are for Windows PowerShell. Run them from the project
root.

### 1. Environment Setup

``` powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, run:

``` powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

### 2. Build the Recommender Models (required before either frontend)

The raw dataset must be available at `data/raw/dataset.csv`.

``` powershell
python scripts\prepare_data.py
python scripts\generate_demo_interactions.py
python scripts\train_models.py
```

The first model-building run may take a few minutes while the full
catalog is processed.

### 3a. Run the Streamlit Interface

``` powershell
streamlit run streamlit_app.py
```

### 3b. Run the Django Web Application

``` powershell
python manage.py migrate
python manage.py runserver
```

Then open `http://127.0.0.1:8000/`. See [WEB_README.md](WEB_README.md)
for full details about the web application.

## Django Web Application

The Django frontend provides a full-featured web interface on top of the
same hybrid recommendation engine used by the Streamlit app.

**Features:**

-   **Song search** with live autocomplete across track names and
    artists
-   **Genre browsing** with a complete genre list from the catalog
-   **Hybrid recommendations** with an adjustable alpha slider
-   **User accounts** with sign-up, login, and logout
-   **Favourites** — save and unsave songs (requires an account)
-   **Search history** — recent recommendation queries are stored per
    user

The web app loads the trained ML models (`models/content.joblib`,
`models/collaborative.joblib`) and the processed track catalog
(`data/processed/tracks.parquet`) lazily on the first request. The
recommender pipeline scripts in Step 2 above must be run before starting
the Django server.

## Optional Evaluation and Tuning

Run these commands after preparing the data and generating the synthetic
interactions. Training artifacts must exist before evaluation.

``` powershell
python scripts\optimize_hybrid.py
python scripts\evaluate_models.py
```

The evaluation script compares:

-   Content-based recommendations
-   Collaborative recommendations
-   Hybrid recommendations
-   A popularity-based baseline

It reports Precision@10, Recall@10, MAP@10, NDCG@10, and catalogue
coverage. The script saves the metrics to
`models/evaluation_metrics.csv` and the chart to
`models/evaluation_chart.png`.

The optimization script prints the alpha value with the highest average
NDCG@10 on its held-out validation examples. The shown training script
does not automatically store this optimized alpha in the saved models;
the application must be configured to use it if desired.

## Limitations

-   Collaborative filtering is trained on synthetic, genre-biased
    interactions rather than real listener histories.
-   Evaluation metrics measure performance on held-out synthetic events
    and demonstrate the pipeline; they do not establish real-world
    Spotify recommendation performance.
-   Recommendations depend on the supplied catalog and its available
    metadata.
