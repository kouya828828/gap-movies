# reviews/models.py - Gap Movies 完全版（全機能保持 + 100点満点対応）
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Person(models.Model):
    """映画製作者 (監督、キャスト、脚本家など)"""
    name = models.CharField(max_length=100, verbose_name="氏名")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "人物"
        verbose_name_plural = "人物"


class Movie(models.Model):
    """映画モデル"""
    title = models.CharField(max_length=200, verbose_name="タイトル")
    original_title = models.CharField(max_length=200, blank=True, verbose_name="原題")
    overview = models.TextField(blank=True, verbose_name="概要")
    release_date = models.DateField(null=True, blank=True, verbose_name="公開日")
    runtime = models.IntegerField(null=True, blank=True, verbose_name="上映時間（分）")
    poster_path = models.CharField(max_length=200, blank=True, verbose_name="ポスター画像パス")
    backdrop_path = models.CharField(max_length=200, blank=True, verbose_name="背景画像パス")
    vote_average = models.FloatField(default=0, verbose_name="TMDb評価")
    vote_count = models.IntegerField(default=0, verbose_name="TMDb投票数")
    popularity = models.FloatField(default=0, verbose_name="人気度")
    trailer_url = models.URLField(blank=True, verbose_name="予告編URL")
    trailer_key = models.CharField(max_length=50, blank=True, verbose_name="YouTube動画ID")  
    tmdb_id = models.IntegerField(unique=True, null=True, blank=True, verbose_name="TMDb ID")
    jp_release_date = models.DateField(null=True, blank=True, verbose_name="日本公開日")
    is_now_playing_jp = models.BooleanField(default=False, verbose_name="日本で現在公開中")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="登録日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    director = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='directed_movies', verbose_name="監督")
    cast = models.ManyToManyField(Person, related_name='acted_movies', blank=True, verbose_name="キャスト")

    def __str__(self):
        return self.title

    def average_score(self):
        """総合平均スコア（反映スコアベース）"""
        reviews = self.review_set.filter(satisfaction__isnull=False)
        if reviews.exists():
            total = sum(review.reflected_score() for review in reviews)
            return round(total / reviews.count(), 1)
        return None

    def movie_buff_score(self):
        """映画通ユーザーの平均スコア"""
        reviews = self.review_set.filter(
            satisfaction__isnull=False, 
            user__userprofile__is_movie_buff=True
        )
        if reviews.exists():
            total = sum(review.reflected_score() for review in reviews)
            return round(total / reviews.count(), 1)
        return None

    def casual_user_score(self):
        """ライトユーザーの平均スコア"""
        reviews = self.review_set.filter(
            satisfaction__isnull=False, 
            user__userprofile__is_movie_buff=False
        )
        if reviews.exists():
            total = sum(review.reflected_score() for review in reviews)
            return round(total / reviews.count(), 1)
        return None

    def golden_score(self):
        """ゴールデンスコア（期待と満足のバランス）"""
        reviews = self.review_set.filter(satisfaction__isnull=False)
        if reviews.exists():
            total = sum(review.golden_score() for review in reviews)
            return round(total / reviews.count(), 1)
        return None

    def expectation_reaction(self):
        """期待との比較テキスト"""
        reviews = self.review_set.filter(satisfaction__isnull=False)
        if not reviews.exists():
            return None
        
        total = reviews.count()
        positive = sum(1 for r in reviews if r.gap_score() and r.gap_score() > 10)
        negative = sum(1 for r in reviews if r.gap_score() and r.gap_score() < -10)
        
        positive_percent = round((positive / total) * 100)
        negative_percent = round((negative / total) * 100)
        
        if positive_percent > 50:
            return f"この作品は期待より良かった人が多いです（{positive_percent}%の人が期待を超えたと評価）"
        elif negative_percent > 50:
            return f"この作品は期待してたより良くなかった人が多いです（{negative_percent}%の人が期待を下回ったと評価）"
        else:
            neutral_percent = 100 - positive_percent - negative_percent
            return f"この作品は期待通りだった人が多いです（{neutral_percent}%の人が期待通りと評価）"

    @property
    def review_count(self):
        """レビュー数"""
        return self.review_set.filter(satisfaction__isnull=False).count()

    @property
    def movie_buff_review_count(self):
        """映画通のレビュー数"""
        return self.review_set.filter(
            satisfaction__isnull=False,
            user__userprofile__is_movie_buff=True
        ).count()

    @property
    def casual_review_count(self):
        """ライトユーザーのレビュー数"""
        return self.review_set.filter(
            satisfaction__isnull=False,
            user__userprofile__is_movie_buff=False
        ).count()

    class Meta:
        verbose_name = "映画"
        verbose_name_plural = "映画"
        ordering = ['-popularity']


class UserProfile(models.Model):
    """ユーザープロフィール"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True, verbose_name="自己紹介")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="アバター")
    is_movie_buff = models.BooleanField(default=False, verbose_name="映画通ユーザー")
    notify_on_comment = models.BooleanField(default=True, verbose_name="コメント通知")
    notify_on_like = models.BooleanField(default=True, verbose_name="いいね通知")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="登録日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    def __str__(self):
        return f"{self.user.username}のプロフィール"

    class Meta:
        verbose_name = "ユーザープロフィール"
        verbose_name_plural = "ユーザープロフィール"


class Review(models.Model):
    """レビューモデル（100点満点）"""
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, verbose_name="映画")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ユーザー")
    expectation = models.IntegerField(default=50, verbose_name="期待値メーター（0-100）")
    satisfaction = models.IntegerField(null=True, blank=True, verbose_name="満足度スコア（0-100）")
    review_text = models.TextField(verbose_name="レビュー本文")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="投稿日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    def gap_score(self):
        """ギャップスコア"""
        if self.satisfaction is not None:
            return self.satisfaction - self.expectation
        return None

    def golden_score(self):
        """ゴールデンスコア（期待と満足の平均）"""
        if self.satisfaction is not None:
            return round((self.expectation + self.satisfaction) / 2, 1)
        return None

    def reflected_score(self):
        """映画の総合スコアに反映される点数"""
        if self.satisfaction is None:
            return self.expectation
        
        gap = self.satisfaction - self.expectation
        
        if gap > 0:  # 期待を超えた
            score = self.satisfaction + (gap * 0.5)
            return min(100, round(score, 1))
        elif gap == 0:  # 期待通り
            return self.satisfaction
        else:  # 期待を下回った
            score = self.satisfaction + (gap * 0.5)
            return max(0, round(score, 1))

    def gap_badge(self):
        """ギャップバッジのテキスト"""
        gap = self.gap_score()
        if gap is None:
            return None
        
        if gap >= 30:
            return "期待を大きく超えた"
        elif gap >= 10:
            return "期待を超えた"
        elif gap >= -9:
            return "期待通り"
        elif gap >= -29:
            return "ちょっと期待外れ"
        else:
            return "かなり期待外れ"

    def gap_badge_class(self):
        """ギャップバッジのCSSクラス"""
        gap = self.gap_score()
        if gap is None:
            return "secondary"
        
        if gap >= 30:
            return "success"
        elif gap >= 10:
            return "info"
        elif gap >= -9:
            return "warning"
        elif gap >= -29:
            return "danger"
        else:
            return "dark"

    def __str__(self):
        return f"{self.user.username}の{self.movie.title}レビュー"

    class Meta:
        verbose_name = "レビュー"
        verbose_name_plural = "レビュー"
        ordering = ['-created_at']
        unique_together = ['movie', 'user']


class CriticReview(models.Model):
    """映画評論家レビュー"""
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, verbose_name="映画")
    critic_name = models.CharField(max_length=100, verbose_name="評論家名")
    publication = models.CharField(max_length=100, blank=True, verbose_name="掲載メディア")
    rating = models.IntegerField(verbose_name="評価（0-100）")
    review_text = models.TextField(verbose_name="レビュー本文")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="投稿日時")

    def __str__(self):
        return f"{self.critic_name}の{self.movie.title}レビュー"

    class Meta:
        verbose_name = "評論家レビュー"
        verbose_name_plural = "評論家レビュー"
        ordering = ['-created_at']


class WatchStatus(models.Model):
    """視聴ステータス"""
    WATCHED = 'watched'
    WATCHING = 'watching'
    WANT_TO_WATCH = 'want_to_watch'

    STATUS_CHOICES = [
        (WATCHED, '見た'),
        (WATCHING, '見てる'),
        (WANT_TO_WATCH, '見たい'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ユーザー")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, verbose_name="映画")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="ステータス")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="登録日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    def __str__(self):
        return f"{self.user.username} - {self.movie.title} ({self.get_status_display()})"

    class Meta:
        verbose_name = "視聴ステータス"
        verbose_name_plural = "視聴ステータス"
        unique_together = ['user', 'movie']


class Favorite(models.Model):
    """お気に入り"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ユーザー")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, verbose_name="映画")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="登録日時")

    def __str__(self):
        return f"{self.user.username}のお気に入り: {self.movie.title}"

    class Meta:
        verbose_name = "お気に入り"
        verbose_name_plural = "お気に入り"
        unique_together = ['user', 'movie']


class Column(models.Model):
    """コラム"""
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="著者")
    title = models.CharField(max_length=200, verbose_name="タイトル")
    content = models.TextField(verbose_name="本文")
    thumbnail = models.ImageField(upload_to='column_thumbnails/', blank=True, null=True, verbose_name="サムネイル")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="投稿日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "コラム"
        verbose_name_plural = "コラム"
        ordering = ['-created_at']


class Comment(models.Model):
    """コメント（レビューまたはコラムに対して）"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ユーザー")
    review = models.ForeignKey(Review, on_delete=models.CASCADE, null=True, blank=True, 
                               related_name='comments', verbose_name="レビュー")
    column = models.ForeignKey(Column, on_delete=models.CASCADE, null=True, blank=True,
                               related_name='comments', verbose_name="コラム")
    content = models.TextField(verbose_name="コメント内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="投稿日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    def __str__(self):
        return f"{self.user.username}のコメント: {self.content[:20]}"

    class Meta:
        verbose_name = "コメント"
        verbose_name_plural = "コメント"
        ordering = ['created_at']


class Like(models.Model):
    """コラムへのいいね"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ユーザー")
    column = models.ForeignKey(Column, on_delete=models.CASCADE, related_name='likes', verbose_name="コラム")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="登録日時")

    def __str__(self):
        return f"{self.user.username}が{self.column.title}にいいね"

    class Meta:
        verbose_name = "いいね"
        verbose_name_plural = "いいね"
        unique_together = ['user', 'column']


class ReviewLike(models.Model):
    """レビューへのいいね"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ユーザー")
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='likes', verbose_name="レビュー")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="登録日時")

    def __str__(self):
        return f"{self.user.username}が{self.review}にいいね"

    class Meta:
        verbose_name = "レビューいいね"
        verbose_name_plural = "レビューいいね"
        unique_together = ['user', 'review']


class Follow(models.Model):
    """ユーザーフォロー"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following', verbose_name="フォローする人")
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers', verbose_name="フォローされる人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="フォロー日時")

    def __str__(self):
        return f"{self.follower.username}が{self.following.username}をフォロー"

    class Meta:
        verbose_name = "フォロー"
        verbose_name_plural = "フォロー"
        unique_together = ['follower', 'following']


class Notification(models.Model):
    """通知"""
    NOTIFICATION_TYPES = [
        ('comment', 'コメント'),
        ('like', 'いいね'),
        ('follow', 'フォロー'),
        ('review_like', 'レビューいいね'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name="受信者")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="送信者")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, verbose_name="通知タイプ")
    content = models.TextField(verbose_name="通知内容")
    link = models.CharField(max_length=200, blank=True, verbose_name="リンク")
    is_read = models.BooleanField(default=False, verbose_name="既読")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")

    # 通知の対象オブジェクト
    review = models.ForeignKey(Review, on_delete=models.CASCADE, null=True, blank=True, verbose_name="レビュー")
    column = models.ForeignKey(Column, on_delete=models.CASCADE, null=True, blank=True, verbose_name="コラム")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, verbose_name="コメント")

    def __str__(self):
        return f"{self.recipient.username}への通知: {self.content[:30]}"

    class Meta:
        verbose_name = "通知"
        verbose_name_plural = "通知"
        ordering = ['-created_at']


class Report(models.Model):
    """通報"""
    REPORT_REASONS = [
        ('spam', 'スパム'),
        ('harassment', 'ハラスメント'),
        ('inappropriate', '不適切な内容'),
        ('other', 'その他'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="通報者")
    content_type = models.CharField(max_length=50, verbose_name="コンテンツタイプ")
    object_id = models.PositiveIntegerField(verbose_name="オブジェクトID")
    reason = models.CharField(max_length=20, choices=REPORT_REASONS, verbose_name="理由")
    description = models.TextField(verbose_name="詳細")
    is_resolved = models.BooleanField(default=False, verbose_name="解決済み")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="通報日時")

    def __str__(self):
        return f"{self.reporter.username}からの通報"

    class Meta:
        verbose_name = "通報"
        verbose_name_plural = "通報"
        ordering = ['-created_at']


class MovieRecommendation(models.Model):
    """映画レコメンド"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ユーザー")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, verbose_name="映画")
    score = models.FloatField(verbose_name="レコメンドスコア")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")

    def __str__(self):
        return f"{self.user.username}への{self.movie.title}レコメンド"

    class Meta:
        verbose_name = "映画レコメンド"
        verbose_name_plural = "映画レコメンド"
        ordering = ['-score']

class Discussion(models.Model):
    """みんなの声 - ユーザー掲示板"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="投稿者")
    title = models.CharField(max_length=200, verbose_name="タイトル")
    content = models.TextField(verbose_name="本文")
    movie = models.ForeignKey(Movie, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='discussions', verbose_name="関連映画")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="投稿日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "みんなの声投稿"
        verbose_name_plural = "みんなの声投稿"
        ordering = ['-created_at']


class DiscussionComment(models.Model):
    """みんなの声へのコメント"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ユーザー")
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, 
                                   related_name='comments', verbose_name="投稿")
    content = models.TextField(verbose_name="コメント内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="投稿日時")

    def __str__(self):
        return f"{self.user.username}のコメント"

    class Meta:
        verbose_name = "みんなの声コメント"
        verbose_name_plural = "みんなの声コメント"
        ordering = ['created_at']

class FanArt(models.Model):
    """ファンアート"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="投稿者")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, 
                                related_name='fanarts', verbose_name="関連映画")
    image = models.ImageField(upload_to='fanarts/', verbose_name="アート画像")
    title = models.CharField(max_length=200, verbose_name="タイトル")
    description = models.TextField(max_length=500, blank=True, verbose_name="説明")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="投稿日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    def __str__(self):
        return f"{self.user.username}の{self.movie.title}ファンアート"

    class Meta:
        verbose_name = "ファンアート"
        verbose_name_plural = "ファンアート"
        ordering = ['-created_at']


class FanArtLike(models.Model):
    """ファンアートへのいいね"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ユーザー")
    fanart = models.ForeignKey(FanArt, on_delete=models.CASCADE, 
                               related_name='likes', verbose_name="ファンアート")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="登録日時")

    def __str__(self):
        return f"{self.user.username}が{self.fanart}にいいね"

    class Meta:
        verbose_name = "ファンアートいいね"
        verbose_name_plural = "ファンアートいいね"
        unique_together = ['user', 'fanart']

class ContactMessage(models.Model):
    """問い合わせメッセージ"""
    name = models.CharField('お名前', max_length=100)
    email = models.EmailField('メールアドレス')
    subject = models.CharField('件名', max_length=200)
    message = models.TextField('メッセージ')
    created_at = models.DateTimeField('送信日時', auto_now_add=True)
    is_read = models.BooleanField('既読', default=False)
    
    class Meta:
        verbose_name = '問い合わせ'
        verbose_name_plural = '問い合わせ'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.subject}"