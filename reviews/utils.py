import requests
from decouple import config
import logging

logger = logging.getLogger(__name__)

def fetch_now_playing_movies():
    """TMDbから現在公開中の映画一覧を取得"""
    api_key = config('TMDB_API_KEY', default='')
    
    if not api_key:
        print('❌ TMDB_API_KEY が設定されていません')  # ← 追加
        logger.error('TMDB_API_KEY が設定されていません')
        return []
    
    url = "https://api.themoviedb.org/3/movie/now_playing"
    params = {
        "api_key": api_key,
        "region": "JP",
        "language": "ja-JP",
        "page": 1
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'results' not in data:
            print('❌ TMDb APIからresultsが返されませんでした')  # ← 追加
            logger.warning('TMDb APIからresultsが返されませんでした')
            return []
        
        print(f'✅ TMDbから{len(data["results"])}件の映画を取得しました')  # ← 追加
        logger.info(f'TMDbから{len(data["results"])}件の映画を取得しました')
        return data.get('results', [])
        
    except requests.Timeout:
        print('❌ タイムアウト')  # ← 追加
        logger.error('TMDb APIのリクエストがタイムアウトしました')
        return []
    except requests.RequestException as e:
        print(f'❌ APIエラー: {e}')  # ← 追加
        logger.error(f'TMDb APIエラー: {e}')
        return []
    except ValueError as e:
        print(f'❌ JSONエラー: {e}')  # ← 追加
        logger.error(f'JSONデコードエラー: {e}')
        return []

# ↓↓↓ ここから外に出す（関数の外） ↓↓↓
GENRE_MAP = {
    28: "アクション",
    12: "アドベンチャー",
    16: "アニメーション",
    35: "コメディ",
    80: "犯罪",
    99: "ドキュメンタリー",
    18: "ドラマ",
    10751: "ファミリー",
    14: "ファンタジー",
    36: "歴史",
    27: "ホラー",
    10402: "音楽",
    9648: "ミステリー",
    10749: "ロマンス",
    878: "SF",
    10770: "テレビ映画",
    53: "スリラー",
    10752: "戦争",
    37: "西部劇"
}

def get_genre_names(genre_ids):
    """ジャンルIDのリストをジャンル名のリストに変換"""
    return [GENRE_MAP.get(gid, "その他") for gid in genre_ids]