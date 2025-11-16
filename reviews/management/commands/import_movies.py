# reviews/management/commands/import_movies.py
from django.core.management.base import BaseCommand
from reviews.models import Movie, Person
import requests
import time
from datetime import datetime

class Command(BaseCommand):
    help = 'TMDb APIから映画データを大量取得（日本公開日優先）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pages',
            type=int,
            default=10,
            help='取得するページ数（1ページ = 20映画）'
        )
        parser.add_argument(
            '--category',
            type=str,
            default='popular',
            choices=['popular', 'top_rated', 'now_playing', 'upcoming'],
            help='取得する映画カテゴリ'
        )

    def get_japan_release_date(self, release_dates_data):
        """日本の公開日を取得"""
        results = release_dates_data.get('results', [])
        
        # まず日本（JP）の公開日を探す
        for country_data in results:
            if country_data.get('iso_3166_1') == 'JP':
                release_dates = country_data.get('release_dates', [])
                if release_dates:
                    # 劇場公開（type=3）を優先
                    for release in release_dates:
                        if release.get('type') == 3:  # Theatrical
                            return release.get('release_date', '').split('T')[0]
                    # なければ最初の公開日
                    return release_dates[0].get('release_date', '').split('T')[0]
        
        return None

    def handle(self, *args, **options):
        API_KEY = 'b9760e1d8453603c1da9bfe8a42be001'

        if API_KEY == 'YOUR_TMDB_API_KEY_HERE':
            self.stdout.write(self.style.ERROR('❌ エラー: APIキーが設定されていません！'))
            return

        pages = options['pages']
        category = options['category']

        category_names = {
            'popular': '人気映画',
            'top_rated': '高評価映画',
            'now_playing': '上映中',
            'upcoming': '公開予定'
        }

        self.stdout.write(self.style.WARNING(f'\n📥 {category_names[category]}を{pages}ページ分取得します...'))
        self.stdout.write(self.style.WARNING(f'⏱️  推定所要時間: 約{pages * 0.4:.1f}分\n'))

        total_imported = 0
        total_skipped = 0
        total_jp_release = 0

        for page in range(1, pages + 1):
            self.stdout.write(f'📄 ページ {page}/{pages} を処理中...')

            # TMDb APIから映画リストを取得
            url = f'https://api.themoviedb.org/3/movie/{category}'
            params = {
                'api_key': API_KEY,
                'language': 'ja-JP',
                'page': page
            }

            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f'❌ APIエラー: {e}'))
                continue

            data = response.json()
            movies = data.get('results', [])

            if not movies:
                self.stdout.write(self.style.WARNING('⚠️  このページには映画がありません'))
                continue

            for movie_data in movies:
                tmdb_id = movie_data.get('id')

                # すでに存在する映画はスキップ
                if Movie.objects.filter(tmdb_id=tmdb_id).exists():
                    total_skipped += 1
                    continue

                # 映画の詳細情報を取得（release_datesも含む）
                detail_url = f'https://api.themoviedb.org/3/movie/{tmdb_id}'
                detail_params = {
                    'api_key': API_KEY,
                    'language': 'ja-JP',
                    'append_to_response': 'credits,videos,release_dates'
                }

                try:
                    detail_response = requests.get(detail_url, params=detail_params, timeout=10)
                    detail_response.raise_for_status()
                except requests.exceptions.RequestException:
                    continue

                detail_data = detail_response.json()

                # 日本の公開日を取得
                japan_release_date = self.get_japan_release_date(
                    detail_data.get('release_dates', {})
                )
                
                # 日本の公開日がなければデフォルトの公開日を使用
                release_date = japan_release_date or detail_data.get('release_date')
                
                if japan_release_date:
                    total_jp_release += 1

                # 予告編URLを取得
                trailer_url = ''
                videos = detail_data.get('videos', {}).get('results', [])
                for video in videos:
                    if video.get('type') == 'Trailer' and video.get('site') == 'YouTube':
                        trailer_key = video.get('key')
                        trailer_url = f'https://www.youtube.com/embed/{trailer_key}'
                        break

                # 映画を作成
                try:
                    movie = Movie.objects.create(
                        tmdb_id=tmdb_id,
                        title=detail_data.get('title', ''),
                        original_title=detail_data.get('original_title', ''),
                        overview=detail_data.get('overview', ''),
                        release_date=release_date or None,
                        runtime=detail_data.get('runtime'),
                        poster_path=detail_data.get('poster_path', ''),
                        backdrop_path=detail_data.get('backdrop_path', ''),
                        popularity=detail_data.get('popularity', 0),
                        vote_average=detail_data.get('vote_average', 0),
                        vote_count=detail_data.get('vote_count', 0),
                        trailer_url=trailer_url
                    )

                    # 監督を追加
                    credits = detail_data.get('credits', {})
                    crew = credits.get('crew', [])
                    for person in crew:
                        if person.get('job') == 'Director':
                            director, created = Person.objects.get_or_create(
                                name=person.get('name')
                            )
                            movie.director = director
                            movie.save()
                            break

                    # キャストを追加（上位5人）
                    cast = credits.get('cast', [])[:5]
                    for person_data in cast:
                        person, created = Person.objects.get_or_create(
                            name=person_data.get('name')
                        )
                        movie.cast.add(person)

                    total_imported += 1
                    jp_flag = '🇯🇵' if japan_release_date else '🌏'
                    self.stdout.write(self.style.SUCCESS(f'  ✅ {jp_flag} {movie.title}'))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ❌ エラー: {e}'))
                    continue

                # API制限対策で少し待機
                time.sleep(0.25)

            # ページ間の待機
            if page < pages:
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS(f'\n🎉 完了！'))
        self.stdout.write(self.style.SUCCESS(f'📥 新規追加: {total_imported}本'))
        self.stdout.write(self.style.SUCCESS(f'🇯🇵 日本公開日: {total_jp_release}本'))
        self.stdout.write(self.style.WARNING(f'⏭️  スキップ: {total_skipped}本（既存）'))

        if total_imported > 0:
            self.stdout.write(self.style.SUCCESS(f'\n✨ {total_imported}本の映画がGap Moviesに追加されました！'))