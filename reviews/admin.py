from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import (
    Movie, Review, CriticReview, Person, Favorite, Column, WatchStatus, Like,
    UserProfile, Comment, Notification, Follow, Report, ReviewLike,
    MovieRecommendation, FanArt, FanArtLike, ContactMessage, Discussion, DiscussionComment
)
from cloudinary_storage.storage import MediaCloudinaryStorage

# Summernote用のカスタムストレージ設定
class CustomSummernoteModelAdmin(SummernoteModelAdmin):
    summernote_fields = '__all__'
    
    def get_summernote_config(self):
        config = super().get_summernote_config()
        config['storage'] = MediaCloudinaryStorage()  # ← Cloudinaryストレージを強制
        return config

# 既存のモデル登録をそのまま維持

# Movie Admin
@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'release_date', 'jp_release_date', 'is_now_playing_jp', 'director', 'popularity']
    list_filter = ['release_date', 'is_now_playing_jp']
    search_fields = ['title', 'original_title', 'director__name']
    filter_horizontal = ['cast']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('tmdb_id', 'title', 'original_title', 'overview', 'release_date', 'runtime')
        }),
        ('日本公開情報', {  # ★ 追加
            'fields': ('jp_release_date', 'is_now_playing_jp'),
            'description': '「日本で現在公開中」にチェックすると、上映中ページに優先表示されます'
        }),
        ('画像', {
            'fields': ('poster_path', 'backdrop_path', 'trailer_url', 'trailer_key') 
        }),
        ('TMDb統計', {
            'fields': ('popularity', 'vote_average', 'vote_count')
        }),
        ('スタッフ・キャスト', {
            'fields': ('director', 'cast')
        }),
        ('システム情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Review Admin
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'expectation', 'satisfaction', 'gap_score', 'created_at']
    list_filter = ['created_at', 'expectation', 'satisfaction']
    search_fields = ['user__username', 'movie__title', 'review_text']
    readonly_fields = ['created_at', 'updated_at']
    
    def gap_score(self, obj):
        return obj.gap_score
    gap_score.short_description = 'ギャップスコア'


# CriticReview Admin
@admin.register(CriticReview)
class CriticReviewAdmin(admin.ModelAdmin):
    list_display = ['critic_name', 'movie', 'publication', 'rating', 'created_at']
    list_filter = ['rating', 'publication', 'created_at']
    search_fields = ['critic_name', 'publication', 'movie__title']
    readonly_fields = ['created_at']


# Person Admin
@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


# Favorite Admin
@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'movie__title']
    readonly_fields = ['created_at']


# Column Admin
@admin.register(Column)
class ColumnAdmin(SummernoteModelAdmin):
    summernote_fields = ('content',) 
    list_display = ['title', 'author', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'author__username', 'content']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('author', 'title', 'content')
        }),
        ('システム情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# WatchStatus Admin
@admin.register(WatchStatus)
class WatchStatusAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'movie__title']
    readonly_fields = ['created_at', 'updated_at']


# Like Admin
@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'column', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'column__title']
    readonly_fields = ['created_at']


# UserProfile Admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_movie_buff', 'created_at']
    list_filter = ['is_movie_buff', 'notify_on_comment', 'notify_on_like']
    search_fields = ['user__username', 'bio']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('ユーザー情報', {
            'fields': ('user', 'bio', 'avatar', 'is_movie_buff')
        }),
        ('通知設定', {
            'fields': ('notify_on_comment', 'notify_on_like')
        }),
        ('システム情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Comment Admin
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_target', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'content']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_target(self, obj):
        if obj.review:
            return f"レビュー: {obj.review}"
        elif obj.column:
            return f"コラム: {obj.column.title}"
        return "不明"
    get_target.short_description = 'コメント先'


# Notification Admin
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'sender', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'sender__username', 'content']
    readonly_fields = ['created_at']


# Follow Admin
@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__username', 'following__username']
    readonly_fields = ['created_at']


# Report Admin
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'content_type', 'reason', 'is_resolved', 'created_at']
    list_filter = ['content_type', 'reason', 'is_resolved', 'created_at']
    search_fields = ['reporter__username', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('報告情報', {
            'fields': ('reporter', 'content_type', 'object_id', 'reason', 'description')
        }),
        ('ステータス', {
            'fields': ('is_resolved',)
        }),
        ('システム情報', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# ReviewLike Admin
@admin.register(ReviewLike)
class ReviewLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'review', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'review__movie__title']
    readonly_fields = ['created_at']


# MovieRecommendation Admin
@admin.register(MovieRecommendation)
class MovieRecommendationAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'score', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'movie__title']
    readonly_fields = ['created_at']


# FanArt Admin
@admin.register(FanArt)
class FanArtAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'movie', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'user__username', 'movie__title', 'description']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('基本情報', {
            'fields': ('user', 'movie', 'title', 'description', 'image')
        }),
        ('システム情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# FanArtLike Admin
@admin.register(FanArtLike)
class FanArtLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'fanart', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'fanart__title']
    readonly_fields = ['created_at']


# ContactMessage Admin
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['created_at']
    
    # 既読/未読の切り替えアクション
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "選択した問い合わせを既読にする"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
    mark_as_unread.short_description = "選択した問い合わせを未読にする"


# Discussion Admin (みんなの声)
@admin.register(Discussion)
class DiscussionAdmin(SummernoteModelAdmin):
    summernote_fields = ('content',)  # Summernoteエディタを適用
    list_display = ['title', 'user', 'movie', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'user__username', 'movie__title', 'content']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('user', 'movie', 'title', 'content')
        }),
        ('システム情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )