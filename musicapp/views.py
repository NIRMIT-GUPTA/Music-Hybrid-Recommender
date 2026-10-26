"""JSON endpoints and the one-page interface for the recommender."""
import json

from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .engine import get_data, get_engine
from .forms import SignUpForm
from .models import Favourite, SearchHistory


def _session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def _payload(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return None


def _plain(value):
    """Convert pandas/numpy scalar values into JSON-safe Python values."""
    return value.item() if hasattr(value, "item") else value


def _record(row):
    return {key: _plain(value) for key, value in row.items()}


def _login_response():
    return JsonResponse({"error": "Please sign in to save favourites and search history.", "requires_login": True}, status=401)


@ensure_csrf_cookie
def index(request):
    """Render the page and ensure AJAX POST requests receive a CSRF cookie."""
    return render(request, "musicapp/index.html")


def signup(request):
    if request.user.is_authenticated:
        return redirect("index")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("index")
    return render(request, "registration/signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("index")
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect(request.POST.get("next") or "index")
    return render(request, "registration/login.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("index")


@require_GET
def search_tracks(request):
    query = request.GET.get("q", "").strip()
    if len(query) < 2:
        return JsonResponse({"tracks": []})
    data = get_data()
    matches = data[
        data["track_name"].str.contains(query, case=False, na=False, regex=False)
        | data["artists"].str.contains(query, case=False, na=False, regex=False)
    ][["track_id", "track_name", "artists", "track_genre"]].head(15)
    return JsonResponse({"tracks": [_record(row) for row in matches.to_dict("records")]})


@require_GET
def genres(request):
    values = sorted(str(genre) for genre in get_data()["track_genre"].dropna().unique())
    return JsonResponse({"genres": values})


@require_POST
def recommend(request):
    body = _payload(request)
    if body is None:
        return JsonResponse({"error": "Request body must be valid JSON."}, status=400)
    mode = body.get("mode")
    if mode not in ("song", "genre"):
        return JsonResponse({"error": "mode must be 'song' or 'genre'."}, status=400)
    default_alpha = 0.6 if mode == "song" else 0.5
    try:
        alpha = float(body.get("alpha", default_alpha))
    except (TypeError, ValueError):
        return JsonResponse({"error": "alpha must be a number from 0 to 1."}, status=400)
    if not 0 <= alpha <= 1:
        return JsonResponse({"error": "alpha must be between 0 and 1."}, status=400)

    data, engine = get_data(), get_engine()
    if mode == "song":
        track_id = str(body.get("track_id", "")).strip()
        selected = data[data["track_id"].astype(str) == track_id]
        if not track_id or selected.empty:
            return JsonResponse({"error": "Please choose a valid song."}, status=400)
        try:
            results = engine.recommend_by_song(track_id, top_n=10, alpha=alpha)
        except KeyError:
            return JsonResponse({"error": "That song is not available for recommendations."}, status=400)
        song = selected.iloc[0]
        if request.user.is_authenticated:
            SearchHistory.objects.create(user=request.user, mode="song", query_label=str(song["track_name"]), track_id=track_id)
    else:
        genre = str(body.get("genre", "")).strip()
        if not genre or genre not in set(data["track_genre"].astype(str)):
            return JsonResponse({"error": "Please choose a valid genre."}, status=400)
        try:
            results = engine.recommend_by_genre(genre, top_n=10, alpha=alpha)
        except KeyError:
            return JsonResponse({"error": "That genre is not available for recommendations."}, status=400)
        if request.user.is_authenticated:
            SearchHistory.objects.create(user=request.user, mode="genre", query_label=genre, genre=genre)
    return JsonResponse({"results": [_record(row) for row in results.to_dict("records")]})


@require_POST
def toggle_favourite(request):
    if not request.user.is_authenticated:
        return _login_response()
    body = _payload(request)
    if body is None:
        return JsonResponse({"error": "Request body must be valid JSON."}, status=400)
    track_id = str(body.get("track_id", "")).strip()
    row = get_data()[get_data()["track_id"].astype(str) == track_id]
    if not track_id or row.empty:
        return JsonResponse({"error": "Please choose a valid song."}, status=400)
    favourite = Favourite.objects.filter(user=request.user, track_id=track_id).first()
    if favourite:
        favourite.delete()
        return JsonResponse({"favourited": False, "track_id": track_id})
    song = row.iloc[0]
    Favourite.objects.create(user=request.user, track_id=track_id, track_name=str(song["track_name"]), artists=str(song["artists"]), track_genre=str(song["track_genre"]))
    return JsonResponse({"favourited": True, "track_id": track_id})


@require_GET
def favourites(request):
    if not request.user.is_authenticated:
        return JsonResponse({"favourites": [], "requires_login": True})
    rows = Favourite.objects.filter(user=request.user)
    return JsonResponse({"favourites": [{"track_id": item.track_id, "track_name": item.track_name, "artists": item.artists, "track_genre": item.track_genre} for item in rows]})


@require_GET
def history(request):
    if not request.user.is_authenticated:
        return JsonResponse({"history": [], "requires_login": True})
    rows = SearchHistory.objects.filter(user=request.user)[:10]
    return JsonResponse({"history": [{"mode": item.mode, "query_label": item.query_label, "track_id": item.track_id, "genre": item.genre} for item in rows]})
