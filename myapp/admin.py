from django.contrib import admin
from .models import UserProfile, KakaoProfile, Project, NewsPost

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'created_at')
    search_fields = ('user__username', 'phone_number')

@admin.register(KakaoProfile)
class KakaoProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'kakao_id', 'nickname')
    search_fields = ('user__username', 'kakao_id', 'nickname')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title', 'description')

@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'date')
    search_fields = ('title', 'content')
