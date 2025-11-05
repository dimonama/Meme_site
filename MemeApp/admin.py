from django.contrib import admin
from .models import Meme, UserProfile

class MemeAdmin(admin.ModelAdmin):
    list_display = ['title', 'meme_type', 'uploaded_by', 'uploaded_at', 'views']
    list_filter = ['meme_type', 'uploaded_at']
    search_fields = ['title', 'description']
    readonly_fields = ['uploaded_at', 'views']

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'created_at']
    search_fields = ['user__username', 'bio', 'location']

# Реєструємо моделі без декораторів
admin.site.register(Meme, MemeAdmin)
admin.site.register(UserProfile, UserProfileAdmin)