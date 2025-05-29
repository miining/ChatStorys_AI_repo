"""
음악 추천 시스템

Algorithm 1, 3, 4를 구현하여 감정 기반 음악 추천을 수행합니다.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from .emotion_analyzer import EmotionAnalyzer

class MusicRecommender:
    def __init__(self):
        """
        음악 추천 시스템 초기화
        """
        self.emotion_analyzer = EmotionAnalyzer()
        
        # Algorithm 4: get_music_features_for_emotion의 weight_table
        self.weight_table = {
            'anger': [0.14, 0.86, 0.95, 0.05, 0.25, 0.75, 0.20],
            'sadness': [0.82, 0.18, 0.14, 0.86, 0.05, 0.95, 0.05],
            'anxiety': [0.22, 0.78, 0.92, 0.08, 0.17, 0.83, 0.10],
            'hurt': [0.75, 0.25, 0.20, 0.80, 0.13, 0.88, 0.05],
            'embarrassment': [0.33, 0.67, 0.89, 0.11, 0.33, 0.67, 0.15],
            'joy': [0.50, 0.50, 0.09, 0.91, 0.95, 0.05, 0.90]
        }
        
        # 특성 이름들
        self.feature_names = ['acoustic', 'electronic', 'aggressive', 'relaxed', 'happy', 'sad', 'party']

    def get_music_features_for_emotion(self, emotion: str) -> List[float]:
        """
        Algorithm 4: 감정에 대한 음악 특성 벡터 반환
        
        Args:
            emotion (str): 감정 ('anger', 'sadness', 'anxiety', 'hurt', 'embarrassment', 'joy')
            
        Returns:
            List[float]: 음악 특성 벡터 [acoustic, electronic, aggressive, relaxed, happy, sad, party]
        """
        # 1. Define weight_table as in Table 1 (이미 __init__에서 정의됨)
        
        # 2. // 1. Lookup the row for the given emotion
        # 3. music_features ← weight_table[emotion]
        if emotion in self.weight_table:
            music_features = self.weight_table[emotion].copy()
        else:
            # 기본값으로 joy 사용
            music_features = self.weight_table['joy'].copy()
            
        # 4. return music_features
        return music_features

    def cosine_similarity(self, vecA: List[float], vecB: List[float]) -> float:
        """
        Algorithm 3: 두 벡터 간의 코사인 유사도 계산
        
        Args:
            vecA (List[float]): 벡터 A
            vecB (List[float]): 벡터 B
            
        Returns:
            float: 코사인 유사도 (0-1)
        """
        # NumPy 배열로 변환
        vec_a = np.array(vecA)
        vec_b = np.array(vecB)
        
        # 1. dot_prod ← dot(vecA, vecB)
        dot_prod = np.dot(vec_a, vec_b)
        
        # 2. normA ← magnitude(vecA)
        norm_a = np.linalg.norm(vec_a)
        
        # 3. normB ← magnitude(vecB)
        norm_b = np.linalg.norm(vec_b)
        
        # 4. if normA = 0 or normB = 0 then
        # 5.   return 0
        # 6. end if
        if norm_a == 0 or norm_b == 0:
            return 0
            
        # 7. similarity ← dot_prod / (normA * normB)
        similarity = dot_prod / (norm_a * norm_b)
        
        # 8. return similarity
        return float(similarity)

    def recommend_music(self, userID: str, novelContents: str, musicDB: List[Dict], N: int = 5) -> List[Dict]:
        """
        Algorithm 1: 소설 내용 기반 음악 추천
        
        Args:
            userID (str): 사용자 ID
            novelContents (str): 소설 내용
            musicDB (List[Dict]): 음악 데이터베이스 (각 항목은 songName, artist, feature_vector 포함)
            N (int): 추천할 음악 개수 (기본값: 5)
            
        Returns:
            List[Dict]: 추천된 음악 리스트
        """
        try:
            # 1. // 1. Perform emotion analysis
            # 2. emotion_probs ← analyze_emotion_with_KoELECTRA(novelContents)
            emotion_probs = self.emotion_analyzer.analyze_emotion_with_KoELECTRA(novelContents)
            
            # 3. // 2. Select the top emotion
            # 4. top_emotion ← arg max_e emotion_probs[e]
            if not emotion_probs:
                top_emotion = 'joy'  # 기본값
            else:
                top_emotion = max(emotion_probs.items(), key=lambda x: x[1])[0]
            
            # 5. // 3. Lookup music feature vector for that emotion
            # 6. target_features ← get_music_features_for_emotion(top_emotion)
            target_features = self.get_music_features_for_emotion(top_emotion)
            
            # 7. // 4. Load song feature vectors from the music database
            # 8. musicDB ← load_music_database_features() {Each entry: (songName, artist, feature_vector)}
            # (musicDB는 이미 매개변수로 전달됨)
            
            # 9. // 5. Compute cosine similarity
            # 10. similarity_list ← ∅
            similarity_list = []
            
            # 11. for all entry in musicDB do
            for entry in musicDB:
                # 12. songName ← entry.songName
                songName = entry.get('songName', entry.get('musicTitle', 'Unknown'))
                
                # 13. artist ← entry.artist
                artist = entry.get('artist', entry.get('composer', 'Unknown'))
                
                # 14. song_feats ← entry.feature_vector
                song_feats = entry.get('feature_vector', [])
                
                # feature_vector가 없는 경우 기본값 사용
                if not song_feats or len(song_feats) != 7:
                    song_feats = [0.5] * 7  # 중간값으로 초기화
                
                # 15. sim ← cosine_similarity(target_features, song_feats)
                sim = self.cosine_similarity(target_features, song_feats)
                
                # 16. similarity_list.append((songID, sim))
                similarity_list.append({
                    'songName': songName,
                    'artist': artist,
                    'similarity': sim,
                    'emotion': top_emotion,
                    'original_entry': entry
                })
            # 17. end for
            
            # 18. // 6. Sort by similarity and pick top N
            # 19. sort(similarity_list) by similarity desc
            similarity_list.sort(key=lambda x: x['similarity'], reverse=True)
            
            # 20. N ← 5
            # 21. recommendedList ← similarity_list[1..N]
            recommendedList = similarity_list[:N]
            
            # 22. // 7. Optionally save recommendation history
            # 23. save_user_recommendation_history(userID, recommendedList)
            # (선택사항으로 구현하지 않음)
            
            # 24. return recommendedList
            return recommendedList
            
        except Exception as e:
            print(f"음악 추천 오류: {str(e)}")
            return []

    def save_user_recommendation_history(self, userID: str, recommendedList: List[Dict]) -> bool:
        """
        사용자 추천 기록 저장 (선택사항)
        
        Args:
            userID (str): 사용자 ID
            recommendedList (List[Dict]): 추천된 음악 리스트
            
        Returns:
            bool: 저장 성공 여부
        """
        # 실제 구현에서는 데이터베이스에 저장
        print(f"사용자 {userID}의 추천 기록 저장: {len(recommendedList)}개 음악")
        return True

    def get_emotion_music_mapping(self) -> Dict[str, List[float]]:
        """
        감정별 음악 특성 매핑 테이블 반환
        
        Returns:
            Dict[str, List[float]]: 감정별 음악 특성 딕셔너리
        """
        return self.weight_table.copy()

    def analyze_music_features(self, music_features: List[float]) -> Dict[str, str]:
        """
        음악 특성 벡터를 분석하여 특성 설명 반환
        
        Args:
            music_features (List[float]): 음악 특성 벡터
            
        Returns:
            Dict[str, str]: 특성별 설명
        """
        if len(music_features) != 7:
            return {"error": "Invalid feature vector length"}
            
        descriptions = {}
        for i, (feature_name, value) in enumerate(zip(self.feature_names, music_features)):
            if value > 0.7:
                descriptions[feature_name] = "High"
            elif value > 0.3:
                descriptions[feature_name] = "Medium"
            else:
                descriptions[feature_name] = "Low"
                
        return descriptions


# 사용 예시
if __name__ == "__main__":
    # 음악 추천 시스템 초기화
    recommender = MusicRecommender()
    
    # 테스트용 음악 데이터베이스
    test_musicDB = [
        {
            'songName': '행복한 노래',
            'artist': '작곡가1',
            'feature_vector': [0.3, 0.4, 0.1, 0.9, 0.95, 0.1, 0.8]  # joy 특성과 유사
        },
        {
            'songName': '슬픈 발라드',
            'artist': '작곡가2',
            'feature_vector': [0.8, 0.2, 0.1, 0.8, 0.1, 0.9, 0.1]  # sadness 특성과 유사
        },
        {
            'songName': '격렬한 록',
            'artist': '작곡가3',
            'feature_vector': [0.1, 0.9, 0.95, 0.1, 0.3, 0.7, 0.2]  # anger 특성과 유사
        }
    ]
    
    # 테스트 소설 내용
    test_novel = "오늘은 정말 기쁜 날이었다. 모든 일이 잘 풀렸고 친구들과 즐거운 시간을 보냈다."
    
    # 음악 추천 테스트
    recommendations = recommender.recommend_music("user123", test_novel, test_musicDB, N=3)
    
    print("🎵 음악 추천 결과:")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['songName']} - {rec['artist']}")
        print(f"   감정: {rec['emotion']}, 유사도: {rec['similarity']:.3f}")
    
    # 감정별 특성 테스트
    print("\n📊 감정별 음악 특성:")
    for emotion in ['joy', 'sadness', 'anger']:
        features = recommender.get_music_features_for_emotion(emotion)
        print(f"{emotion}: {features}")
        analysis = recommender.analyze_music_features(features)
        print(f"  분석: {analysis}")
        print()