import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from typing import Dict, List, Union
import os

class EmotionAnalyzer:
    def __init__(self, model_path: str = "outputs/koelectra_emotion"):
        """
        감정 분석을 위한 KoELECTRA 모델 초기화
        
        Args:
            model_path (str): KoELECTRA 모델이 저장된 경로
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()
        
        # 감정 레이블 정의
        self.emotion_labels = [
            '기쁨', '슬픔', '분노', '불안', '상처', '당황', '기대', '지루함'
        ]
    
    def analyze_text(self, text: str) -> Dict[str, float]:
        """
        텍스트의 감정을 분석하여 각 감정의 확률값을 반환
        
        Args:
            text (str): 분석할 텍스트
            
        Returns:
            Dict[str, float]: 감정별 확률값을 담은 딕셔너리
        """
        # 텍스트 토큰화
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)
        
        # 감정 분석 수행
        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = torch.softmax(outputs.logits, dim=1)
            
        # 결과를 딕셔너리로 변환
        emotion_scores = {
            label: float(prob)
            for label, prob in zip(self.emotion_labels, probabilities[0])
        }
        
        return emotion_scores
    
    def analyze_texts(self, texts: List[str]) -> List[Dict[str, float]]:
        """
        여러 텍스트의 감정을 분석
        
        Args:
            texts (List[str]): 분석할 텍스트 리스트
            
        Returns:
            List[Dict[str, float]]: 각 텍스트별 감정 확률값 리스트
        """
        return [self.analyze_text(text) for text in texts]
    
    def get_dominant_emotion(self, text: str) -> str:
        """
        텍스트의 주요 감정을 반환
        
        Args:
            text (str): 분석할 텍스트
            
        Returns:
            str: 가장 높은 확률을 가진 감정 레이블
        """
        emotion_scores = self.analyze_text(text)
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
        emotion_scores = self.analyze_text(text)
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
    
    # 전체 감정 분석
    emotions = analyzer.analyze_text(test_text)
    print("\n전체 감정 분석 결과:")
    for emotion, score in emotions.items():
        print(f"{emotion}: {score:.3f}")
    
    # 주요 감정
    dominant = analyzer.get_dominant_emotion(test_text)
    print(f"\n주요 감정: {dominant}")
    
    # 상위 3개 감정
    top_emotions = analyzer.get_emotion_distribution(test_text, top_k=3)
    print("\n상위 3개 감정:")
    for emotion, score in top_emotions:
        print(f"{emotion}: {score:.3f}") 