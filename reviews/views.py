from django.shortcuts import render, get_object_or_404, redirect 
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from datetime import date
from django_summernote.widgets import SummernoteWidget
# Summernote用カスタムアップロードビュー
from django_summernote.views import SummernoteUploadAttachment
from cloudinary_storage.storage import MediaCloudinaryStorage

from .models import (
    Movie, Person, Review, CriticReview, Column, Discussion, DiscussionComment,
    Follow, Report, ReviewLike, MovieRecommendation, Favorite, WatchStatus,
    UserProfile, Comment, Notification, Like, FanArt, FanArtLike
)
from .forms import (
    ReviewForm, DiscussionForm, DiscussionCommentForm, SignUpForm,
    ColumnForm, UserProfileForm, UserEditForm, CommentForm, FanArtForm
)

def movie_list(request):
    """映画一覧を表示 - ページネーション付き + 検索機能"""
    query = request.GET.get('q', '')
    
    movies = Movie.objects.all().order_by('-popularity')  # 人気度順
    
    # 検索機能
    if query:
        movies = movies.filter(
            Q(title__icontains=query) | Q(original_title__icontains=query)
        )
    
    # ページネーション（30件ずつ）
    paginator = Paginator(movies, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'movies': page_obj,
        'page_obj': page_obj,
        'query': query,
    }
    
    return render(request, 'reviews/movie_list.html', context)

def movie_detail(request, pk):
    """映画詳細とレビュー投稿処理"""
    movie = get_object_or_404(Movie, pk=pk)
    today = date.today() 
    
    # お気に入り状態を確認
    is_favorite = False
    if request.user.is_authenticated:
        from .models import Favorite
        is_favorite = Favorite.objects.filter(user=request.user, movie=movie).exists()
    
    # ユーザーが既にこの映画にレビューを投稿済みか確認
    has_reviewed = False
    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(user=request.user, movie=movie).first()
        has_reviewed = user_review is not None
    
    error_message = None
    
    if request.method == 'POST':
        # ログインチェック
        if not request.user.is_authenticated:
            error_message = "レビューを投稿するにはログインが必要です"
        else:
            form = ReviewForm(request.POST, instance=user_review)
            if form.is_valid():
                review = form.save(commit=False)
                review.user = request.user
                review.movie = movie
                review.save()
                return redirect('movie_detail', pk=pk)
    
    # フォームを表示
    if request.user.is_authenticated:
        form = ReviewForm(instance=user_review)
    else:
        form = None

    # レビュー取得
    reviews = Review.objects.filter(movie=movie).order_by('-created_at')
    
    # 視聴ステータスを確認
    from .models import WatchStatus
    watch_status = None
    if request.user.is_authenticated:
        watch_status = WatchStatus.objects.filter(user=request.user, movie=movie).first()
    
    context = {
        'movie': movie,
        'reviews': reviews,
        'form': form,
        'is_favorite': is_favorite,
        'has_reviewed': has_reviewed,
        'error_message': error_message,
        'watch_status': watch_status,
        'user_review': user_review,
        'today': today,  
    }
    
    return render(request, 'reviews/movie_detail.html', context)


def person_movie_list(request, pk):
    """特定の人物（監督など）に関連する映画一覧"""
    person = get_object_or_404(Person, pk=pk)
    movies = person.directed_movies.all()
    
    context = {
        'person': person,
        'movies': movies,
        'is_person_list': True,
    }
    
    return render(request, 'reviews/movie_list.html', context)


def now_playing_view(request):
    """上映中の映画と公開予定の映画を表示（タブ切り替え対応）"""
    from datetime import date, timedelta
    
    today = date.today()
    status = request.GET.get('status', 'now_playing')  # デフォルトは「現在公開中」
    
    if status == 'coming_soon':
        # 公開予定: jp_release_dateが今日より未来の映画
        movies = Movie.objects.filter(
            jp_release_date__gt=today
        ).order_by('jp_release_date')  # 公開日が近い順
    else:
        # 現在公開中
        two_months_ago = today - timedelta(days=60)
        
        # 方法1: 管理画面で手動選択した映画（最優先）
        manually_selected = Movie.objects.filter(
            is_now_playing_jp=True
        ).order_by('-popularity')
        
        # 方法2: jp_release_dateが過去2ヶ月以内の映画（自動）
        auto_selected = Movie.objects.filter(
            jp_release_date__gte=two_months_ago,
            jp_release_date__lte=today
        ).exclude(
            is_now_playing_jp=True  # 手動選択と重複しないように
        ).order_by('-popularity')
        
        # 結合
        from itertools import chain
        movies = list(chain(manually_selected, auto_selected))
        movies = movies[:40]  # 最大40件（手動選択を優先表示）
    
    context = {
        'movies': movies,
        'status': status,
        'last_updated': today,
    }
    
    return render(request, 'reviews/now_playing.html', context)

def create_movie_from_tmdb(request, tmdb_id):
    """TMDbの映画をMovieモデルに保存"""
    # この機能は後で実装
    return redirect('home')


def home(request):
    """ホームページ - 予告編・コラム・人気映画・最新レビューを表示"""
    # 特集映画（予告編用）- TMDbの人気映画上位5本
    featured_movies = Movie.objects.filter(
        popularity__gt=50
    ).order_by('-popularity')[:5]
    
    # 埋め込みURLを視聴用URLに変換
    for movie in featured_movies:
        if movie.trailer_url and '/embed/' in movie.trailer_url:
            # https://www.youtube.com/embed/XXX → https://www.youtube.com/watch?v=XXX
            movie.watch_url = movie.trailer_url.replace('/embed/', '/watch?v=')
        else:
            movie.watch_url = movie.trailer_url
    
    # 人気映画ランキング（人気度順 - レビューがなくても表示）
    popular_movies = Movie.objects.order_by('-popularity')[:6]
    
    # 最新レビュー
    recent_reviews = Review.objects.select_related(
        'user', 'movie'
    ).order_by('-created_at')[:6]
    
    # 最新コラム
    recent_columns = Column.objects.select_related(
        'author'
    ).order_by('-created_at')[:6]
    
    context = {
        'featured_movies': featured_movies,
        'popular_movies': popular_movies,
        'recent_reviews': recent_reviews,
        'recent_columns': recent_columns,
    }
    return render(request, 'reviews/home.html', context)



def signup_view(request):
    """ユーザー登録"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # UserProfileを作成してis_movie_buffを保存
            is_movie_buff = form.cleaned_data.get('is_movie_buff', False)
            UserProfile.objects.create(user=user, is_movie_buff=is_movie_buff)
            
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    
    return render(request, 'reviews/signup.html', {'form': form})


def login_view(request):
    """ログイン"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    
    return render(request, 'reviews/login.html', {'form': form})


def logout_view(request):
    """ログアウト"""
    logout(request)
    return redirect('home')



@login_required
def toggle_favorite(request, movie_id):
    """お気に入りの追加/削除を切り替え"""
    movie = get_object_or_404(Movie, pk=movie_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, movie=movie)
    
    if not created:
        favorite.delete()
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def my_page(request):
    """マイページ - お気に入りとレビュー履歴"""
    from .models import WatchStatus, UserProfile
    
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # お気に入り映画
    favorites = Favorite.objects.filter(user=request.user).select_related('movie')
    
    # 自分のレビュー
    my_reviews = Review.objects.filter(user=request.user).select_related('movie')
    
    # 観た映画
    watched_movies = WatchStatus.objects.filter(user=request.user, status='watched').select_related('movie')
    
    # 観たい映画
    want_to_watch_movies = WatchStatus.objects.filter(user=request.user, status='want_to_watch').select_related('movie')
    
    context = {
        'profile': profile,
        'favorites': favorites,
        'my_reviews': my_reviews,
        'watched_movies': watched_movies,
        'want_to_watch_movies': want_to_watch_movies,
    }
    
    return render(request, 'reviews/my_page.html', context)


def search(request):
    """映画検索機能"""
    query = request.GET.get('q', '')
    results = Movie.objects.all()
    
    # テキスト検索
    if query:
        results = results.filter(
            Q(title__icontains=query) | 
            Q(director__name__icontains=query) |
            Q(cast__name__icontains=query)
        ).distinct()
    
    context = {
        'query': query,
        'results': results,
        'result_count': results.count(),
    }
    
    return render(request, 'reviews/search_results.html', context)



def column_list(request):
    """コラム一覧ページ - ページネーション付き"""
    from .models import Like
    
    columns = Column.objects.all().order_by('-created_at')
    
    liked_column_ids = []
    if request.user.is_authenticated:
        liked_column_ids = Like.objects.filter(user=request.user).values_list('column_id', flat=True)
    
    paginator = Paginator(columns, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'columns': page_obj,
        'page_obj': page_obj,
        'liked_column_ids': liked_column_ids,
    }
    
    return render(request, 'reviews/column_list.html', context)


def column_detail(request, pk):
    """コラム詳細ページ"""
    from .models import Like
    
    column = get_object_or_404(Column, pk=pk)
    
    is_liked = False
    if request.user.is_authenticated:
        is_liked = Like.objects.filter(user=request.user, column=column).exists()
    
    context = {
        'column': column,
        'is_liked': is_liked,
    }
    
    return render(request, 'reviews/column_detail.html', context)


@login_required
def column_create(request):
    """コラム投稿ページ"""
    if request.method == 'POST':
        form = ColumnForm(request.POST, request.FILES)
        if form.is_valid():
            column = form.save(commit=False)
            column.author = request.user
            column.save()
            return redirect('column_detail', pk=column.pk)
    else:
        form = ColumnForm()
    
    return render(request, 'reviews/column_create.html', {'form': form})


@login_required
def column_edit(request, pk):
    """コラム編集ページ"""
    column = get_object_or_404(Column, pk=pk)
    
    if column.author != request.user:
        return redirect('column_detail', pk=pk)
    
    if request.method == 'POST':
        form = ColumnForm(request.POST, request.FILES, instance=column)
        if form.is_valid():
            form.save()
            return redirect('column_detail', pk=column.pk)
    else:
        form = ColumnForm(instance=column)
    
    context = {
        'form': form,
        'column': column,
    }
    
    return render(request, 'reviews/column_edit.html', context)


@login_required
def column_delete(request, pk):
    """コラム削除"""
    column = get_object_or_404(Column, pk=pk)
    
    if column.author == request.user:
        column.delete()
    
    return redirect('column_list')


@login_required
def review_edit(request, pk):
    """レビュー編集ページ"""
    review = get_object_or_404(Review, pk=pk)
    
    if review.user != request.user:
        return redirect('movie_detail', pk=review.movie.pk)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            return redirect('movie_detail', pk=review.movie.pk)
    
    context = {
        'review': review,
        'form': ReviewForm(instance=review),
    }
    
    return render(request, 'reviews/review_edit.html', context)


@login_required
def review_delete(request, pk):
    """レビュー削除"""
    review = get_object_or_404(Review, pk=pk)
    movie_pk = review.movie.pk
    
    if review.user == request.user:
        review.delete()
    
    return redirect('movie_detail', pk=movie_pk)


@login_required
def toggle_watch_status(request, movie_id):
    """観た/観たいステータスの切り替え"""
    movie = get_object_or_404(Movie, pk=movie_id)
    status_type = request.POST.get('status', 'watched')
    
    from .models import WatchStatus
    
    watch_status = WatchStatus.objects.filter(user=request.user, movie=movie).first()
    
    if watch_status:
        if watch_status.status == status_type:
            watch_status.delete()
        else:
            watch_status.status = status_type
            watch_status.save()
    else:
        WatchStatus.objects.create(user=request.user, movie=movie, status=status_type)
    
    return redirect('movie_detail', pk=movie_id)


@login_required
def toggle_like(request, column_id):
    """コラムへのいいねをトグル"""
    from .models import Notification, Like, UserProfile
    column = get_object_or_404(Column, pk=column_id)
    like, created = Like.objects.get_or_create(user=request.user, column=column)
    
    if not created:
        like.delete()
    else:
        if column.author != request.user:
            author_profile, _ = UserProfile.objects.get_or_create(user=column.author)
            if author_profile.notify_on_like:
                Notification.objects.create(
                    recipient=column.author,
                    sender=request.user,
                    notification_type='like',
                    content=f'{request.user.username}があなたのコラムにいいねしました'
                )
    
    return redirect('column_detail', pk=column.pk)



def user_profile(request, username):
    """ユーザープロフィール表示"""
    user = get_object_or_404(User, username=username)
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    user_reviews = Review.objects.filter(user=user).select_related('movie').order_by('-created_at')
    user_columns = Column.objects.filter(author=user).order_by('-created_at')
    user_favorites = Favorite.objects.filter(user=user).select_related('movie')
    
    # フォロー情報
    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=user
        ).exists()
    
    follower_count = user.followers.count()
    following_count = user.following.count()
    
    context = {
        'profile_user': user,
        'profile': profile,
        'user_reviews': user_reviews,
        'user_columns': user_columns,
        'user_favorites': user_favorites,
        'is_following': is_following,
        'follower_count': follower_count,
        'following_count': following_count,
    }
    
    return render(request, 'reviews/profile.html', context)


@login_required
def edit_profile(request):
    """プロフィール編集"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('user_profile', username=request.user.username)
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'reviews/edit_profile.html', context)


@login_required
def add_comment_to_review(request, review_id):
    """レビューにコメントを追加"""
    review = get_object_or_404(Review, pk=review_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.review = review
            comment.save()
            return redirect('movie_detail', pk=review.movie.pk)
    
    return redirect('movie_detail', pk=review.movie.pk)


@login_required
def add_comment_to_column(request, column_id):
    """コラムにコメントを追加"""
    from .models import Notification
    column = get_object_or_404(Column, pk=column_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.column = column
            comment.save()
            
            if column.author != request.user:
                author_profile, _ = UserProfile.objects.get_or_create(user=column.author)
                if author_profile.notify_on_comment:
                    Notification.objects.create(
                        recipient=column.author,
                        sender=request.user,
                        notification_type='comment',
                        content=f'{request.user.username}があなたのコラムにコメントしました',
                        column=column,
                        comment=comment
                    )
            
            return redirect('column_detail', pk=column.pk)
    
    return redirect('column_detail', pk=column.pk)


@login_required
def delete_comment(request, comment_id):
    """コメントを削除"""
    comment = get_object_or_404(Comment, pk=comment_id)
    
    if comment.user == request.user:
        if comment.review:
            movie_pk = comment.review.movie.pk
            comment.delete()
            return redirect('movie_detail', pk=movie_pk)
        elif comment.column:
            column_pk = comment.column.pk
            comment.delete()
            return redirect('column_detail', pk=column_pk)
    
    return redirect('home')



@login_required
def notification_list(request):
    """通知一覧ページ"""
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    
    context = {
        'notifications': notifications,
    }
    
    return render(request, 'reviews/notification_list.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """通知を既読にする"""
    notification = get_object_or_404(Notification, pk=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    return redirect('notification_list')


# ========================================
# 🆕 Phase 11: フォロー機能
# ========================================

@login_required
def toggle_follow(request, username):
    """フォロー/アンフォローを切り替え"""
    from django.contrib import messages
    target_user = get_object_or_404(User, username=username)
    
    # 自分自身はフォローできない
    if request.user == target_user:
        messages.error(request, '自分自身をフォローすることはできません')
        return redirect('user_profile', username=username)
    
    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=target_user
    )
    
    if not created:
        follow.delete()
    else:
        Notification.objects.create(
            recipient=target_user,
            sender=request.user,
            notification_type='follow',
            content=f'{request.user.username}があなたをフォローしました'
        )
    
    return redirect('user_profile', username=username)


@login_required
def following_list(request, username):
    """フォロー中のユーザー一覧"""
    user = get_object_or_404(User, username=username)
    following = Follow.objects.filter(follower=user).select_related('following')
    
    return render(request, 'reviews/following_list.html', {
        'profile_user': user,
        'following': following,
    })


@login_required
def followers_list(request, username):
    """フォロワー一覧"""
    user = get_object_or_404(User, username=username)
    followers = Follow.objects.filter(following=user).select_related('follower')
    
    return render(request, 'reviews/followers_list.html', {
        'profile_user': user,
        'followers': followers,
    })


@login_required
def activity_feed(request):
    """フォロー中のユーザーのアクティビティフィード"""
    following_users = request.user.following.values_list('following', flat=True)
    
    reviews = Review.objects.filter(user__in=following_users).order_by('-created_at')[:20]
    columns = Column.objects.filter(author__in=following_users).order_by('-created_at')[:20]
    
    activities = []
    for review in reviews:
        activities.append({
            'type': 'review',
            'user': review.user,
            'content': review,
            'created_at': review.created_at,
        })
    
    for column in columns:
        activities.append({
            'type': 'column',
            'user': column.author,
            'content': column,
            'created_at': column.created_at,
        })
    
    activities.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render(request, 'reviews/activity_feed.html', {
        'activities': activities[:30],
    })


# ========================================
# 🆕 Phase 12: 報告機能
# ========================================

@login_required
def report_content(request):
    """コンテンツ報告"""
    from django.contrib import messages
    from django.http import JsonResponse
    
    if request.method == 'POST':
        content_type = request.POST.get('content_type')
        object_id = request.POST.get('object_id')
        reason = request.POST.get('reason')
        description = request.POST.get('description', '')
        
        Report.objects.create(
            reporter=request.user,
            content_type=content_type,
            object_id=int(object_id),
            reason=reason,
            description=description
        )
        
        messages.success(request, '報告を送信しました。ご協力ありがとうございます。')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    
    content_type = request.GET.get('content_type')
    object_id = request.GET.get('object_id')
    
    return render(request, 'reviews/report_form.html', {
        'content_type': content_type,
        'object_id': object_id,
    })


# ========================================
# 🆕 Phase 13: レビューへのいいね
# ========================================

@login_required
def toggle_review_like(request, review_id):
    """レビューへのいいね/いいね解除"""
    from django.http import JsonResponse
    review = get_object_or_404(Review, id=review_id)
    
    like, created = ReviewLike.objects.get_or_create(
        user=request.user,
        review=review
    )
    
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
        
        if review.user != request.user:
            Notification.objects.create(
                recipient=review.user,
                sender=request.user,
                notification_type='like',
                content=f'{request.user.username}があなたのレビューにいいねしました',
                review=review
            )
    
    like_count = review.likes.count()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'liked': liked,
            'like_count': like_count,
        })
    
    return redirect('movie_detail', pk=review.movie.id)


# ========================================
# 🆕 Phase 14: おすすめ映画機能
# ========================================

@login_required
def recommended_movies(request):
    """ユーザーにおすすめの映画を表示"""
    user = request.user
    
    user_reviews = Review.objects.filter(user=user)
    
    if user_reviews.count() == 0:
        recommended = Movie.objects.annotate(
            review_count=models.Count('review')  # ← 'reviews' → 'review'に戻す
        ).filter(review_count__gt=0).order_by('-review_count')[:20]
        
        return render(request, 'reviews/recommended.html', {
            'movies': recommended,
            'message': '人気の映画からおすすめをピックアップしました',
        })
    
    high_satisfaction_reviews = user_reviews.filter(satisfaction__gte=70)
    favorite_directors = set()
    
    for review in high_satisfaction_reviews:
        if review.movie.director:
            favorite_directors.add(review.movie.director)
    
    recommended = Movie.objects.filter(
        director__in=favorite_directors
    ).exclude(
        id__in=user_reviews.values_list('movie_id', flat=True)
    ).annotate(
        review_count=models.Count('review')  # ← 'reviews' → 'review'に戻す
    ).order_by('-review_count')[:20]
    
    return render(request, 'reviews/recommended.html', {
        'movies': recommended,
        'message': 'あなたの好みに基づいたおすすめ',
    })


# ========================================
# お問い合わせ
# ========================================

from .models import ContactMessage

def contact(request):
    """お問い合わせフォーム"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        if name and email and subject and message:
            # データベースに保存
            ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            
            # メール送信（既存のコード）
            try:
                send_mail(
                    subject=f'【Gap Movies】{subject}',
                    message=f'お名前: {name}\nメールアドレス: {email}\n\n{message}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.CONTACT_EMAIL],
                    fail_silently=False,
                )
                messages.success(request, 'お問い合わせを送信しました。')
            except Exception as e:
                messages.warning(request, 'お問い合わせは保存されましたが、メール送信に失敗しました。')
            
            return redirect('contact')
        else:
            messages.error(request, 'すべての項目を入力してください。')
    
    return render(request, 'reviews/contact.html')


# ========================================
# 高度な検索機能
# ========================================

def advanced_search(request):
    """高度な検索"""
    query = request.GET.get('q', '')
    year_from = request.GET.get('year_from', '')
    year_to = request.GET.get('year_to', '')
    sort_by = request.GET.get('sort', 'title')
    
    results = Movie.objects.all()
    
    if query:
        results = results.filter(
            Q(title__icontains=query) | 
            Q(director__name__icontains=query) |
            Q(cast__name__icontains=query)
        ).distinct()
    
    if year_from:
        try:
            results = results.filter(release_date__year__gte=int(year_from))
        except (ValueError, TypeError):
            pass
    
    if year_to:
        try:
            results = results.filter(release_date__year__lte=int(year_to))
        except (ValueError, TypeError):
            pass
    
    if sort_by == 'year_desc':
        results = results.order_by('-release_date')
    elif sort_by == 'year_asc':
        results = results.order_by('release_date')
    elif sort_by == 'title':
        results = results.order_by('title')
    
    context = {
        'query': query,
        'year_from': year_from,
        'year_to': year_to,
        'sort_by': sort_by,
        'results': results,
        'result_count': results.count(),
    }
    
    return render(request, 'reviews/advanced_search.html', context)
# ========================================
# みんなの声（掲示板）機能
# ========================================

def discussion_list(request):
    """みんなの声一覧"""
    discussions = Discussion.objects.all().order_by('-created_at')
    
    paginator = Paginator(discussions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'reviews/discussion_list.html', {
        'page_obj': page_obj,
    })


def discussion_detail(request, pk):
    """みんなの声詳細"""
    discussion = get_object_or_404(Discussion, pk=pk)
    comments = discussion.comments.all().order_by('created_at')
    
    if request.method == 'POST' and request.user.is_authenticated:
        form = DiscussionCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.discussion = discussion
            comment.save()
            return redirect('discussion_detail', pk=pk)
    else:
        form = DiscussionCommentForm() if request.user.is_authenticated else None
    
    return render(request, 'reviews/discussion_detail.html', {
        'discussion': discussion,
        'comments': comments,
        'form': form,
    })


@login_required
def discussion_create(request):
    """みんなの声投稿"""
    if request.method == 'POST':
        form = DiscussionForm(request.POST)
        if form.is_valid():
            discussion = form.save(commit=False)
            discussion.user = request.user
            discussion.save()
            return redirect('discussion_detail', pk=discussion.pk)
    else:
        form = DiscussionForm()
    
    return render(request, 'reviews/discussion_create.html', {
        'form': form,
    })


@login_required
def discussion_edit(request, pk):
    """みんなの声編集"""
    discussion = get_object_or_404(Discussion, pk=pk)
    
    if discussion.user != request.user:
        return redirect('discussion_detail', pk=pk)
    
    if request.method == 'POST':
        form = DiscussionForm(request.POST, instance=discussion)
        if form.is_valid():
            form.save()
            return redirect('discussion_detail', pk=pk)
    else:
        form = DiscussionForm(instance=discussion)
    
    return render(request, 'reviews/discussion_edit.html', {
        'form': form,
        'discussion': discussion,
    })


@login_required
def discussion_delete(request, pk):
    """みんなの声削除"""
    discussion = get_object_or_404(Discussion, pk=pk)
    
    if discussion.user == request.user:
        discussion.delete()
    
    return redirect('discussion_list')

# ========================================
# ファンアート機能
# ========================================

def fanart_list(request):
    """ファンアート一覧"""
    fanarts = FanArt.objects.all().select_related('user', 'movie').order_by('-created_at')
    
    # いいね済みのファンアートIDを取得
    liked_fanart_ids = []
    if request.user.is_authenticated:
        liked_fanart_ids = FanArtLike.objects.filter(
            user=request.user
        ).values_list('fanart_id', flat=True)
    
    # ページネーション
    paginator = Paginator(fanarts, 12)  # 12作品ずつ
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'fanarts': page_obj,
        'page_obj': page_obj,
        'liked_fanart_ids': liked_fanart_ids,
    }
    
    return render(request, 'reviews/fanart_list.html', context)


@login_required
def fanart_create(request):
    """ファンアート投稿"""
    if request.method == 'POST':
        form = FanArtForm(request.POST, request.FILES)
        if form.is_valid():
            fanart = form.save(commit=False)
            fanart.user = request.user
            fanart.save()
            return redirect('fanart_list')
    else:
        form = FanArtForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'reviews/fanart_create.html', context)


@login_required
def fanart_delete(request, pk):
    """ファンアート削除"""
    fanart = get_object_or_404(FanArt, pk=pk)
    
    # 投稿者本人のみ削除可能
    if fanart.user == request.user:
        fanart.delete()
    
    return redirect('fanart_list')


@login_required
def toggle_fanart_like(request, fanart_id):
    """ファンアートへのいいね/いいね解除"""
    from django.http import JsonResponse
    
    fanart = get_object_or_404(FanArt, id=fanart_id)
    
    like, created = FanArtLike.objects.get_or_create(
        user=request.user,
        fanart=fanart
    )
    
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    
    like_count = fanart.likes.count()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'liked': liked,
            'like_count': like_count,
        })
    
    return redirect('fanart_list')

class CloudinarySummernoteUploadAttachment(SummernoteUploadAttachment):
    storage = MediaCloudinaryStorage()