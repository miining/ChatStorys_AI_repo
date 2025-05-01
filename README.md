# ChatStorys_AI_repo
koElectra 기반 다중 감정 분석 모델 파인튜닝

개요

koElectra는 한국어에 최적화된 사전 학습 언어 모델로, 본 프로젝트에서는 이를 활용하여 텍스트의 여러 감정을 분류하는 다중 감정 분석(Multi-Emotion Classification) 모델을 fine-tuning 합니다.

목표: 소설, 대화, 리뷰 등 다양한 한국어 텍스트에서 행복(joy), 슬픔(sadness), 분노(anger), 공포(fear), 놀람(surprise), 혐오(disgust) 등 복수의 감정을 자동으로 분류

모델: beomi/KoELECTRA-base-v3-discriminator 기반

주요 기능

다중 라벨(Multi-Label) 분류 지원

사용자 정의 감정 레이블 설정 가능

손쉬운 데이터 전처리 및 토크나이저 설정

다양한 하이퍼파라미터 조정 (학습률, 배치 크기, 에포크 수 등)

학습 중 로그 및 평가 지표(Accuracy, Precision, Recall, F1-Score) 출력

추론 스크립트 제공으로 실시간 예측 가능

요구사항

Python >= 3.7

PyTorch >= 1.10

Transformers >= 4.20.0

Datasets >= 2.0.0

scikit-learn, pandas, numpy, tqdm

pip install torch transformers datasets scikit-learn pandas numpy tqdm

파일 구조

├── README.md              # 프로젝트 설명
├── requirements.txt       # 의존성 목록
├── data/                  # 데이터 디렉토리
│   ├── train.csv          # 학습용 데이터
│   └── val.csv            # 검증용 데이터
├── train.py               # 학습 스크립트
├── inference.py           # 추론 스크립트
└── outputs/               # 학습 결과 모델 저장

데이터 준비

CSV 형식: text, labels 컬럼 필수

text: 분석 대상 문장

labels: 다중 감정을 쉼표로 구분한 문자열 (예: joy, surprise)

레이블 인코딩:

from sklearn.preprocessing import MultiLabelBinarizer

mlb = MultiLabelBinarizer(classes=['joy','sadness','anger','fear','surprise','disgust'])
data['label_vec'] = mlb.fit_transform(data['labels'].str.split(',')).tolist()

train.csv, val.csv 파일로 저장 후 data/ 폴더에 위치

학습 방법

python train.py \
  --model_name_or_path beomi/KoELECTRA-base-v3-discriminator \
  --train_file data/train.csv \
  --validation_file data/val.csv \
  --output_dir outputs/koelectra_emotion \
  --num_labels 6 \
  --task_name multi_label_classification \
  --do_train \
  --do_eval \
  --learning_rate 2e-5 \
  --per_device_train_batch_size 16 \
  --per_device_eval_batch_size 32 \
  --num_train_epochs 5 \
  --logging_steps 100 \
  --evaluation_strategy steps \
  --save_steps 500 \
  --seed 42

손실 함수: BCEWithLogitsLoss (Multi-Label)

평가 지표: accuracy, precision, recall, f1

평가

학습 중 자동으로 검증 데이터를 이용한 평가가 수행됩니다.

최종 평가 리포트는 outputs/koelectra_emotion/eval_results.txt에 저장됩니다.

추론

python inference.py \
  --model_dir outputs/koelectra_emotion \
  --input_text "오늘 기분이 너무 좋아!"

출력 예시:

{
  "joy": 0.87,
  "sadness": 0.03,
  "anger": 0.01,
  "fear": 0.00,
  "surprise": 0.15,
  "disgust": 0.00
}

참고 문헌

koELECTRA: Baek et al., "koELECTRA: Pretraining Text Encoders as Discriminators Rather Than Generators", EKR 2021

Hugging Face Transformers: https://huggingface.co/transformers/
