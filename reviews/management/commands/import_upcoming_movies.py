from django.core.management.base import BaseCommand
from reviews.models import Movie, Person
import requests
from decouple import config
from datetime import datetime

class Command(BaseCommand):
    help = '公開予定の映画をTMDbからインポート'

    def handle(self, *args, **options):
        API_KEY = config('TMDB_API_KEY', default='')
        if not API_KEY:
            self.stdout.write(self.style.ERROR('❌ TMDB_API_KEYが設定されていません'))
            return

        BASE_URL = 'https://api.themoviedb.org/3'
        
        self.stdout.write('📅 公開予定の映画を取得中...')
        
        # 公開予定の映画を取得（最大3ページ）
        movies_data = []
        for page in range(1, 4):
            url = f'{BASE_URL}/movie/upcoming'
            params = {
                'api_key': API_KEY,
                'language': 'ja-JP',
                'page': page,
                'region': 'JP'  # 日本地域の公開予定
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                movies_data.extend(data.get('results', []))
                self.stdout.write(f'  ページ{page}: {len(data.get("results", []))}本取得')
            else:
                self.stdout.write(self.style.WARNING(f'  ページ{page}: 取得失敗'))
        
        self.stdout.write(f'\n✅ 合計 {len(movies_data)} 本の映画を取得しました\n')
        
        # 映画を保存
        created_count = 0
        skipped_count = 0
        
        for movie_data in movies_data:
            tmdb_id = movie_data.get('id')
            
            # 既に存在する映画はスキップ
            if Movie.objects.filter(tmdb_id=tmdb_id).exists():
                skipped_count += 1
                continue
            
            # 詳細情報を取得（日本公開日を含む）
            detail_url = f'{BASE_URL}/movie/{tmdb_id}'
            detail_params = {
                'api_key': API_KEY,
                'language': 'ja-JP',
                'append_to_response': 'release_dates'
            }
            
            detail_response = requests.get(detail_url, params=detail_params)
            if detail_response.status_code != 200:
                continue
            
            detail = detail_response.json()
            
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
            
            # 映画を作成
            try:
                Movie.objects.create(
                    tmdb_id=tmdb_id,
                    title=detail.get('title', ''),
                    original_title=detail.get('original_title', ''),
                    overview=detail.get('overview', ''),
                    release_date=detail.get('release_date'),
                    jp_release_date=jp_release_date,
                    runtime=detail.get('runtime'),
                    poster_path=detail.get('poster_path') or '',  
                    backdrop_path=detail.get('backdrop_path') or '',  
                    popularity=detail.get('popularity', 0),
                    vote_average=detail.get('vote_average', 0),
                    vote_count=detail.get('vote_count', 0)
                )
                created_count += 1
                self.stdout.write(f'  ✅ {detail.get("title")} (公開予定: {jp_release_date or detail.get("release_date")})')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠️ エラー: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n🎉 完了！'))
        self.stdout.write(f'  新規追加: {created_count}本')
        self.stdout.write(f'  スキップ: {skipped_count}本（既存）')