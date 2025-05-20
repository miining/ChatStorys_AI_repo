import requests
import time
import itertools
import pandas as pd
from tqdm import tqdm
import urllib.parse, json

API_KEY = "6a98ccd1bccb3f37b35ffe5a1be904df"
HEADERS  = {"User-Agent": "popular-mbid-scraper/0.1 (jinub080@gmail.com)"}

def lf_get(method, **params):
    url = "https://ws.audioscrobbler.com/2.0/"
    params.update({"method": method, "api_key": API_KEY, "format": "json", "limit": 1000})
    
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request to Last.fm API: {e}")
        return None

def top_tracks_chart():
    print("\nFetching top tracks from charts...")
    data = lf_get("chart.getTopTracks", page=1)
    if not data:
        return
    
    # Limit to first 30 pages
    total_pages = min(int(data["tracks"]["@attr"]["totalPages"]), 30)
    print(f"Fetching {total_pages} pages of chart data...")
    
    for page in tqdm(range(1, total_pages + 1), desc="Chart pages"):
        response = lf_get("chart.getTopTracks", page=page)
        if response and "tracks" in response and "track" in response["tracks"]:
            yield from response["tracks"]["track"]
        time.sleep(0.25)  # 4 req/s

def top_tracks_tag(tags):
    print("\nFetching top tracks by tags...")
    for tag in tqdm(tags, desc="Tags"):
        response = lf_get("tag.getTopTracks", tag=tag)
        if response and "toptracks" in response and "track" in response["toptracks"]:
            yield from response["toptracks"]["track"]
        time.sleep(0.25)

def mb_search(track, artist):
    q = f'recording:"{track}" AND artist:"{artist}"'
    url = ("https://musicbrainz.org/ws/2/recording/"
           f"?query={urllib.parse.quote(q)}&limit=1&fmt=json")
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        js = r.json()
        recs = js.get("recordings", [])
        if recs:
            print(f"✓ Found MBID for: {track} - {artist}")
            return recs[0]["id"]
        else:
            print(f"✗ No MBID found for: {track} - {artist}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"! Error searching MBID for {track} - {artist}: {str(e)}")
        return None

def get_acoustic_mood(mbid, offset=0):
    """
    AcousticBrainz API에서 recording MBID에 대한 high-level mood 확률을 가져옵니다.
    
    Parameters:
        mbid (str): MusicBrainz recording MBID (UUID).
        offset (int): 여러 제출(submission)이 있을 때 선택할 문서의 인덱스(기본 0).
    
    Returns:
        dict or None: {
            'mood_acoustic': float,
            'mood_aggressive': float,
            'mood_electronic': float,
            'mood_happy': float,
            'mood_party': float,
            'mood_relaxed': float,
            'mood_sad': float
        }
        혹은 404 등으로 데이터가 없으면 None을 반환합니다.
    """
    url = f"https://acousticbrainz.org/api/v1/{mbid}/high-level"  # :contentReference[oaicite:0]{index=0}
    params = {
        'n': offset,
        'map_classes': 'true'
    }
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'MyApp/1.0 ( jinub080@gmail.com )'
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.HTTPError as e:
        if resp.status_code == 404:
            print(f"[Warning] No high-level data for MBID {mbid}")
            return None
        else:
            print(f"[Error] HTTP {resp.status_code} for MBID {mbid}: {e}")
            return None
    except requests.RequestException as e:
        print(f"[Error] Request failed for MBID {mbid}: {e}")
        return None

    data = resp.json().get('highlevel', {})
    # mood_* 키가 없으면 0 반환
    mood_keys = [
        'mood_acoustic', 'mood_aggressive', 'mood_electronic',
        'mood_happy', 'mood_party', 'mood_relaxed', 'mood_sad'
    ]
    mood_probs = {
        key: data.get(key, {}).get('probability', 0.0)
        for key in mood_keys
    }
    return mood_probs

def main():
    start_time = time.time()
    
    # # 1) 가져오기
    # tags = ["pop", "rock", "hip-hop", "indie", "alternative", "electronic", "edm",
    #         "dance", "rnb", "k-pop", "metal", "jazz", "classical"]

    # print("Starting data collection...")
    # raw = list(itertools.chain(top_tracks_chart(), top_tracks_tag(tags)))

    # # 2) DataFrame 화
    # if not raw:
    #     print("No data collected")
    #     return

    # print("\nProcessing data...")
    # # Convert raw data to proper format
    # processed_data = []
    # for track in raw:
    #     processed_data.append({
    #         'name': track['name'],
    #         'artist': track['artist']['name'] if isinstance(track['artist'], dict) else track['artist'],
    #         'mbid': track.get('mbid', '').strip(),
    #         'listeners': track.get('listeners', 0),
    #         'playcount': track.get('playcount', 0)
    #     })

    # df = (pd.DataFrame(processed_data)
    #       .drop_duplicates(subset=["name", "artist"]))     # 중복 곡 제거

    # print(f"\n수집된 트랙 수: {len(df)}")

    # # Save to CSV
    # print("\nSaving to CSV...")
    # df.to_csv("music_data.csv", index=False)
    
    # # MBID가 비어 있는 곡만 조회
    # missing = df["mbid"].isna() | (df["mbid"] == "")
    # missing_count = missing.sum()
    
    # if missing_count > 0:
    #     print(f"\nMBID가 없는 트랙 수: {missing_count}")
    #     print("MusicBrainz에서 MBID 조회 시작...")
        
    #     success_count = 0
    #     for idx, row in tqdm(df[missing].iterrows(), total=missing_count, desc="MBID 조회"):
    #         mbid = mb_search(row["name"], row["artist"])
    #         if mbid:
    #             df.at[idx, "mbid"] = mbid
    #             success_count += 1
    #         time.sleep(1.1)  # 1 req/s
        
    #     print(f"\nMBID 조회 결과:")
    #     print(f"- 성공: {success_count}")
    #     print(f"- 실패: {missing_count - success_count}")
        
    #     # 업데이트된 데이터 저장
    #     print("\n업데이트된 데이터 저장 중...")
    #     df.to_csv("music_data_with_mbid.csv", index=False)
    #     print("Data saved to music_data_with_mbid.csv")
    
    df = pd.read_csv("music_data_with_mbid.csv")

    # AcousticBrainz에서 mood 데이터 가져오기
    print("\nAcousticBrainz에서 mood 데이터 수집 시작...")
    mood_data = []
    valid_mbids = df[df["mbid"].notna() & (df["mbid"] != "")]
    
    for idx, row in tqdm(valid_mbids.iterrows(), total=len(valid_mbids), desc="Mood 데이터 수집"):
        features = get_acoustic_mood(row["mbid"])
        if features:
            mood_data.append({
                'mbid': row["mbid"],
                'name': row["name"],
                'artist': row["artist"],
                **features
            })
        time.sleep(1.1)  # 1 req/s
    
    # Mood 데이터를 DataFrame으로 변환
    mood_df = pd.DataFrame(mood_data)
    print(f"\nMood 데이터 수집 결과: {len(mood_df)}개 트랙")
    
    # 최종 데이터 저장
    print("\n최종 데이터 저장 중...")
    mood_df.to_csv("music_data_with_mood.csv", index=False)
    print("Data saved to music_data_with_mood.csv")
    
    end_time = time.time()
    print(f"\n완료! 총 소요 시간: {end_time - start_time:.1f}초")

if __name__ == "__main__":
    main()