from django.core.management.base import BaseCommand
from reviews.models import Movie
import requests
from decouple import config
from datetime import datetime

class Command(BaseCommand):
    help = '指定したTMDb IDの映画を個別にインポート'

    def add_arguments(self, parser):
        parser.add_argument('tmdb_id', type=int, help='TMDb ID')

    def handle(self, *args, **options):
        API_KEY = config('TMDB_API_KEY', default='')
        if not API_KEY:
            self.stdout.write(self.style.ERROR('❌ TMDB_API_KEYが設定されていません'))
            return

        tmdb_id = options['tmdb_id']
        BASE_URL = 'https://api.themoviedb.org/3'
        
        self.stdout.write(f'🔍 TMDb ID {tmdb_id} の映画を取得中...')
        
        # 詳細情報を取得
        detail_url = f'{BASE_URL}/movie/{tmdb_id}'
        detail_params = {
            'api_key': API_KEY,
            'language': 'ja-JP',
            'append_to_response': 'release_dates'
        }
        
        response = requests.get(detail_url, params=detail_params)
        if response.status_code != 200:
            self.stdout.write(self.style.ERROR(f'❌ 映画が見つかりません（TMDb ID: {tmdb_id}）'))
            return
        
        detail = response.json()
        
        # 日本公開日を取得
        jp_release_date = None
        release_dates = detail.get('release_dates', {}).get('results', [])
        for country_data in release_dates:
            if country_data.get('iso_3166_1') == 'JP':
                dates = country_data.get('release_dates', [])
                if dates:
                    release_date_str = dates[0].get('release_date', '')
                    if release_date_str:
                        try:
                            jp_release_date = datetime.strptime(
                                release_date_str[:10], '%Y-%m-%d'
                            ).date()
                        except:
                            pass
                break
        
        # 既存の映画があれば更新、なければ作成
            movie, created = Movie.objects.update_or_create(
                tmdb_id=tmdb_id,
                defaults={
                    'title': detail.get('title', ''),
                    'original_title': detail.get('original_title', ''),
                    'overview': detail.get('overview', ''),
                    'release_date': detail.get('release_date'),
                    'jp_release_date': jp_release_date,
                    'runtime': detail.get('runtime'),
                    'poster_path': detail.get('poster_path') or '', 
                    'backdrop_path': detail.get('backdrop_path') or '', 
                    'popularity': detail.get('popularity', 0),
                    'vote_average': detail.get('vote_average', 0),
                    'vote_count': detail.get('vote_count', 0)
                }
            )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ {detail.get("title")} を追加しました'))
        else:
            self.stdout.write(self.style.SUCCESS(f'🔄 {detail.get("title")} を更新しました'))
        
        self.stdout.write(f'  日本公開日: {jp_release_date or "未設定"}')
        self.stdout.write(f'  公開日: {detail.get("release_date")}')