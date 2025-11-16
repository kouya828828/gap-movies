from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('movies/', views.movie_list, name='movie_list'),
    path('reviews/movie/<int:pk>/', views.movie_detail, name='movie_detail'),
    path('reviews/person/<int:pk>/', views.person_movie_list, name='person_movie_list'),
    path('now-playing/', views.now_playing_view, name='now_playing'),
    path('reviews/create-movie/<int:tmdb_id>/', views.create_movie_from_tmdb, name='create_movie_from_tmdb'),
    
    # ユーザー認証
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout_view'),
    
    # お気に入り機能
    path('favorite/toggle/<int:movie_id>/', views.toggle_favorite, name='toggle_favorite'),
    
    # マイページ
    path('my-page/', views.my_page, name='my_page'),
    
    # 検索機能
    path('search/', views.search, name='search'),
    path('advanced-search/', views.advanced_search, name='advanced_search'),
    
    # コラム機能
    path('columns/', views.column_list, name='column_list'),
    path('columns/<int:pk>/', views.column_detail, name='column_detail'),
    path('columns/create/', views.column_create, name='column_create'),
    path('columns/<int:pk>/edit/', views.column_edit, name='column_edit'),
    path('columns/<int:pk>/delete/', views.column_delete, name='column_delete'),
    
    # レビュー編集・削除
    path('review/<int:pk>/edit/', views.review_edit, name='review_edit'),
    path('review/<int:pk>/delete/', views.review_delete, name='review_delete'),
    
    # 視聴ステータス
    path('watch-status/toggle/<int:movie_id>/', views.toggle_watch_status, name='toggle_watch_status'),
    
    # いいね機能
    path('like/toggle/<int:column_id>/', views.toggle_like, name='toggle_like'),
    
    # ユーザープロフィール
    path('user/<str:username>/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # コメント機能
    path('review/<int:review_id>/comment/', views.add_comment_to_review, name='add_comment_to_review'),
    path('column/<int:column_id>/comment/', views.add_comment_to_column, name='add_comment_to_column'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    
    # 通知機能
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # フォロー機能
    path('follow/toggle/<str:username>/', views.toggle_follow, name='toggle_follow'),
    path('user/<str:username>/following/', views.following_list, name='following_list'),
    path('user/<str:username>/followers/', views.followers_list, name='followers_list'),
    path('activity-feed/', views.activity_feed, name='activity_feed'),
    
    # 報告機能
    path('report/', views.report_content, name='report_content'),
    
    # レビューいいね
    path('review/<int:review_id>/like/', views.toggle_review_like, name='toggle_review_like'),
    
    # おすすめ映画
    path('recommended/', views.recommended_movies, name='recommended_movies'),
    
    # お問い合わせ
    path('contact/', views.contact, name='contact'),

    # みんなの声（掲示板）
    path('discussions/', views.discussion_list, name='discussion_list'),
    path('discussions/<int:pk>/', views.discussion_detail, name='discussion_detail'),
    path('discussions/create/', views.discussion_create, name='discussion_create'),
    path('discussions/<int:pk>/edit/', views.discussion_edit, name='discussion_edit'),
    path('discussions/<int:pk>/delete/', views.discussion_delete, name='discussion_delete'),
    
    # ファンアート機能
    path('fanart/', views.fanart_list, name='fanart_list'),
    path('fanart/create/', views.fanart_create, name='fanart_create'),
    path('fanart/<int:pk>/delete/', views.fanart_delete, name='fanart_delete'),
    path('fanart/<int:fanart_id>/like/', views.toggle_fanart_like, name='toggle_fanart_like'),
]