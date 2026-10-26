from django.contrib import admin

from .models import Favourite, SearchHistory

@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ("track_name", "artists", "user", "created_at")
    list_filter = ("track_genre",)
    search_fields = ("track_name", "artists", "user__username")


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ("query_label", "mode", "user", "created_at")
    list_filter = ("mode",)
    search_fields = ("query_label", "user__username")
