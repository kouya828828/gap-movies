# reviews/forms.py - 100点満点スライダー対応
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Review, Column, Comment, UserProfile, Discussion, DiscussionComment, Movie, FanArt


class SignUpForm(UserCreationForm):
    """サインアップフォーム（映画通/ライト選択追加）"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'メールアドレス'
        })
    )
    
    is_movie_buff = forms.BooleanField(
        required=False,
        label='映画通ユーザーとして登録',
        help_text='映画に詳しい方、たくさん映画を見る方はチェックしてください',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'is_movie_buff')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ユーザー名'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'パスワード'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'パスワード（確認）'
        })


class ReviewForm(forms.ModelForm):
    """レビューフォーム（100点満点スライダー）"""
    expectation = forms.IntegerField(
        label='期待値メーター',
        min_value=0,
        max_value=100,
        initial=50,
        help_text='この映画にどれくらい期待していますか？（0-100点）',
        widget=forms.NumberInput(attrs={
            'type': 'range',
            'class': 'form-range expectation-slider',
            'id': 'expectationSlider',
            'step': '1'
        })
    )
    
    satisfaction = forms.IntegerField(
        label='満足度スコア',
        required=False,
        min_value=0,
        max_value=100,
        help_text='実際に見てどうでしたか？（0-100点）',
        widget=forms.NumberInput(attrs={
            'type': 'range',
            'class': 'form-range satisfaction-slider',
            'id': 'satisfactionSlider',
            'step': '1'
        })
    )

    review_text = forms.CharField(
        label='レビュー',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'この映画の感想を書いてください...'
        })
    )

    class Meta:
        model = Review
        fields = ['expectation', 'satisfaction', 'review_text']


class ColumnForm(forms.ModelForm):
    """コラムフォーム"""
    title = forms.CharField(
        label='タイトル',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'コラムのタイトル'
        })
    )

    content = forms.CharField(
        label='本文',
        widget=forms.Textarea(attrs={
            'class': 'form-control summernote',
            'rows': 10
        })
    )

    thumbnail = forms.ImageField(
        label='サムネイル画像',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = Column
        fields = ['title', 'content', 'thumbnail']


class CommentForm(forms.ModelForm):
    """コメントフォーム"""
    content = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'コメントを入力...'
        })
    )

    class Meta:
        model = Comment
        fields = ['content']


class UserProfileForm(forms.ModelForm):
    """ユーザープロフィール編集フォーム"""
    bio = forms.CharField(
        label='自己紹介',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '自己紹介を入力してください'
        })
    )

    avatar = forms.ImageField(
        label='アバター画像',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        })
    )
    
    is_movie_buff = forms.BooleanField(
        label='映画通ユーザー',
        required=False,
        help_text='映画に詳しい、たくさん映画を見る方はチェック',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    notify_on_comment = forms.BooleanField(
        label='コメント通知を受け取る',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    notify_on_like = forms.BooleanField(
        label='いいね通知を受け取る',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    class Meta:
        model = UserProfile
        fields = ['bio', 'avatar', 'is_movie_buff', 'notify_on_comment', 'notify_on_like']


class UserEditForm(forms.ModelForm):
    """ユーザー情報編集フォーム"""
    username = forms.CharField(
        label='ユーザー名',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )

    email = forms.EmailField(
        label='メールアドレス',
        widget=forms.EmailInput(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email']

class DiscussionForm(forms.ModelForm):
    """みんなの声投稿フォーム"""
    title = forms.CharField(
        label='タイトル',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'タイトルを入力...'
        })
    )

    content = forms.CharField(
        label='本文',
        widget=forms.Textarea(attrs={
            'class': 'form-control summernote',  # ← summernoteクラス追加
            'rows': 10
        })
    )

    movie = forms.ModelChoiceField(
        label='関連映画（オプション）',
        queryset=Movie.objects.all().order_by('-popularity')[:50],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = Discussion
        fields = ['title', 'content', 'movie']

class DiscussionCommentForm(forms.ModelForm):
    """みんなの声コメントフォーム"""
    content = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'コメントを入力...'
        })
    )

    class Meta:
        model = DiscussionComment
        fields = ['content']

class FanArtForm(forms.ModelForm):
    """ファンアート投稿フォーム"""
    class Meta:
        model = FanArt
        fields = ['movie', 'image', 'title', 'description']
        widgets = {
            'movie': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': '映画を選択'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'タイトルを入力'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '作品の説明（任意）'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
        labels = {
            'movie': '関連映画',
            'image': 'アート画像',
            'title': 'タイトル',
            'description': '説明'
        }