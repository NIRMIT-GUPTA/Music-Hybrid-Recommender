from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("accounts/signup/", views.signup, name="signup"),
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path("api/search/", views.search_tracks, name="search_tracks"),
    path("api/genres/", views.genres, name="genres"),
    path("api/recommend/", views.recommend, name="recommend"),
    path("api/favourites/toggle/", views.toggle_favourite, name="toggle_favourite"),
    path("api/favourites/", views.favourites, name="favourites"),
    path("api/history/", views.history, name="history"),
]
