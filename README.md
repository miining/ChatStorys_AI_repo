<h1 align="center">🎧 ChatStory AI Module</h1>
<p align="center">
  <i>“Where storytelling meets intelligent emotion-driven music.”</i><br>
  GPT-4o 기반 소설 생성 + 감정 분석 기반 음악 추천 시스템
</p>

---

## 📌 Overview

**ChatStory AI**는 사용자의 입력을 바탕으로 GPT-4o가 소설을 생성하고, 그 내용에 담긴 감정을 분석하여 적절한 음악을 추천하는 AI 기반 모듈입니다.  
감정 분석 모델로는 KoELECTRA를 Fine-tuning하여 사용하며, 음악 추천은 cosine similarity 기반의 emotion-feature 매칭으로 구현됩니다.  

이 프로젝트는 **감성적 일관성과 몰입감 있는 소설 경험**을 사용자에게 제공하는 것을 목표로 합니다.

---

## 🧠 Core Features

### ✍️ GPT-4o 기반 인터랙티브 스토리 생성
- 사용자의 입력 (`userContents`) + 이전 대화 내용 (`previousContents`)
- 장르 요건을 검색하여 구성된 RAG 기반 Prompt
- 소설 일관성을 유지하며 챕터 단위로 생성 및 저장

### 🎭 감정 분석 (KoELECTRA Fine-tuning)
- 사용자 + GPT 대화 내용을 실시간 감정 분석
- 다중 감정 분류 모델 (예: 행복, 슬픔, 분노 등)
- HuggingFace Transformers 기반 Fine-tuning

### 🎵 감정 기반 음악 추천
- KoELECTRA의 감정 출력 벡터와 음악 feature 간 cosine similarity 계산
- Spotify / Last.fm / AcousticBrainz API를 활용한 음악 feature 수집
- 추천 결과는 소설 분위기와 감정을 고려한 음악 리스트 제공

---

## 🧱 System Architecture

User Input
│
└──► RAG-based Prompt Constructor (BM25 + Genre requirements)
│
▼
GPT-4o Prompt (Genre + Previous + User Contents)
│
▼
GPT-4o Story Generator
│
▼
┌────────────────────────────────────────────┐
│ KoELECTRA Sentiment Classifier │
│ - Multi-label emotion prediction │
└────────────────────────────────────────────┘
│
▼
Emotion Vector → Music Feature Matching (Cosine)
│
▼
🎧 Music Recommendation List

---

## 🧰 Tech Stack

- **LLM**: GPT-4o (via API)
- **NLP**: KoELECTRA (Fine-tuning for multi-emotion classification)
- **RAG**: BM25 (Genre requirement DB retrieval)
- **Music**: Spotify API, Last.fm, AcousticBrainz
- **Backend**: Python, FastAPI
- **Data**: MongoDB (chat logs, genre metadata, music metadata)
- **Infra**: Cursor AI, VS Code, Git

---

## 👤 Maintainer / Author

- **Jinwoo Park (박진우)** – Undergraduate Researcher @ Connected Intelligence LAB  
  🔗 [https://www.linkedin.com/in/%EC%A7%84%EC%9A%B0-%EB%B0%95-06b289368/] | 📫 jinub080@gmail.com

---

## 🧪 Future Directions
- Multimodal Emotion Fusion (text + audio + image)
- Story-driven background music generation
- Personalized reader modeling (reader profile → tone adaptation)
