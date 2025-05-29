import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from typing import Dict, List, Union
import os
from dotenv import load_dotenv

load_dotenv()

class EmotionAnalyzer:
    def __init__(self, model_path: str = None):
        """
        감정 분석을 위한 KoELECTRA 모델 초기화
        
        Args:
            model_path (str): KoELECTRA 모델이 저장된 경로
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 환경변수에서 모델 경로 가져오기
        self.model_path = model_path or os.getenv("KOELECTRA_MODEL_PATH", "outputs/koelectra_emotion")
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
        self.model.to(self.device)
        self.model.eval()
        
        # 감정 레이블 정의 (Algorithm 4에 맞춰 조정)
        self.emotion_labels = [
            'anger', 'sadness', 'anxiety', 'hurt', 'embarrassment', 'joy'
        ]
        
        # 한국어-영어 감정 매핑
        self.emotion_mapping = {
            '분노': 'anger',
            '슬픔': 'sadness', 
            '불안': 'anxiety',
            '상처': 'hurt',
            '당황': 'embarrassment',
            '기쁨': 'joy',
            '기대': 'joy',  # 기대는 기쁨으로 매핑
            '지루함': 'sadness'  # 지루함은 슬픔으로 매핑
        }

    def analyze_emotion_with_KoELECTRA(self, text: str) -> Dict[str, float]:
        """
        Algorithm 2: KoELECTRA를 이용한 감정 분석
        
        Args:
            text (str): 분석할 텍스트
            
        Returns:
            Dict[str, float]: 감정별 확률값 (probs)
        """
        # 1. tokens ← tokenizer.encode(text)
        tokens = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)
        
        # 2. outputs ← KoELECTRA_model.predict(tokens)
        with torch.no_grad():
            outputs = self.model(**tokens)
            
        # 3. probs ← softmax(outputs.logits)
        probs = torch.softmax(outputs.logits, dim=1)
        
        # 4. return probs
        emotion_probs = {}
        korean_labels = ['분노', '슬픔', '불안', '상처', '당황', '기쁨', '기대', '지루함']
        
        # 현재 모델이 8개 감정을 출력한다고 가정하고 매핑
        for i, korean_label in enumerate(korean_labels):
            if i < len(probs[0]):
                english_label = self.emotion_mapping.get(korean_label, korean_label)
                emotion_probs[english_label] = float(probs[0][i])
        
        return emotion_probs

    def analyze_emotions(self, text: str) -> Dict:
        """
        음악 추천 시스템을 위한 감정 분석 (main.py에서 사용)
        
        Args:
            text (str): 분석할 텍스트
            
        Returns:
            Dict: dominant_emotion과 confidence를 포함한 결과
        """
        try:
            # KoELECTRA로 감정 분석
            emotion_probs = self.analyze_emotion_with_KoELECTRA(text)
            
            # 최고 감정과 신뢰도 계산
            if emotion_probs:
                dominant_emotion = max(emotion_probs.items(), key=lambda x: x[1])
                return {
                    'dominant_emotion': dominant_emotion[0],
                    'confidence': dominant_emotion[1],
                    'all_emotions': emotion_probs
                }
            else:
                return {
                    'dominant_emotion': 'joy',
                    'confidence': 0.5,
                    'all_emotions': {'joy': 0.5}
                }
                
        except Exception as e:
            print(f"감정 분석 오류: {str(e)}")
            return {
                'dominant_emotion': 'joy',
                'confidence': 0.5,
                'all_emotions': {'joy': 0.5}
            }

    def analyze_text(self, text: str) -> Dict[str, float]:
        """
        텍스트의 감정을 분석하여 각 감정의 확률값을 반환 (기존 호환성 유지)
        """
        return self.analyze_emotion_with_KoELECTRA(text)
    
    def analyze_texts(self, texts: List[str]) -> List[Dict[str, float]]:
        """
        여러 텍스트의 감정을 분석
        
        Args:
            texts (List[str]): 분석할 텍스트 리스트
            
        Returns:
            List[Dict[str, float]]: 각 텍스트별 감정 확률값 리스트
        """
        return [self.analyze_emotion_with_KoELECTRA(text) for text in texts]
    
    def get_dominant_emotion(self, text: str) -> str:
        """
        텍스트의 주요 감정을 반환
        
        Args:
            text (str): 분석할 텍스트
            
        Returns:
            str: 가장 높은 확률을 가진 감정 레이블 (영어)
        """
        emotion_scores = self.analyze_emotion_with_KoELECTRA(text)
        return max(emotion_scores.items(), key=lambda x: x[1])[0]
    
    def get_emotion_distribution(self, text: str, top_k: int = 3) -> List[tuple]:
        """
        텍스트의 상위 k개 감정과 확률값을 반환
        
        Args:
            text (str): 분석할 텍스트
            top_k (int): 반환할 감정의 개수
            
        Returns:
            List[tuple]: (감정, 확률) 튜플의 리스트
        """
        emotion_scores = self.analyze_emotion_with_KoELECTRA(text)
        sorted_emotions = sorted(
            emotion_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_emotions[:top_k]

# 사용 예시
if __name__ == "__main__":
    # 감정 분석기 초기화
    analyzer = EmotionAnalyzer()
    
    # 테스트 텍스트
    test_text = "오늘은 정말 행복한 날이었다. 친구들과 즐거운 시간을 보냈고, 좋은 소식도 들었다."
    
    # Algorithm 2 테스트
    emotions = analyzer.analyze_emotion_with_KoELECTRA(test_text)
    print("\nKoELECTRA 감정 분석 결과:")
    for emotion, score in emotions.items():
        print(f"{emotion}: {score:.3f}")
    
    # 음악 추천용 분석
    result = analyzer.analyze_emotions(test_text)
    print(f"\n주요 감정: {result['dominant_emotion']} (신뢰도: {result['confidence']:.3f})")
    
    # 주요 감정
    dominant = analyzer.get_dominant_emotion(test_text)
    print(f"\n주요 감정: {dominant}")
    
    # 상위 3개 감정
    top_emotions = analyzer.get_emotion_distribution(test_text, top_k=3)
    print("\n상위 3개 감정:")
    for emotion, score in top_emotions:
        print(f"{emotion}: {score:.3f}") 