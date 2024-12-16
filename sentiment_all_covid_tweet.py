import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from tqdm import tqdm

# 1. 데이터 로드
df = pd.read_csv("covid19_tweets.csv")

# 2. 모델 및 토크나이저 로드
model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# 3. 파이프라인 설정
sentiment_pipe = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

# 4. 감성 분석 함수 정의
def get_sentiment(text):
    # sentiment_pipe 결과 예시: [{'label': 'positive', 'score': 0.998...}]
    result = sentiment_pipe(text[:512])  # 512토큰 이내로 잘라내기 (긴 텍스트 처리 시)
    return result[0]['label']

# 5. 감성 분석 적용 (tqdm 추가)
tqdm.pandas()
df['sentiment'] = df['text'].progress_apply(get_sentiment)

# 6. 결과 저장
df.to_csv("covid19_tweets_with_sentiment.csv", index=False)

print("감성 분석이 완료되었습니다. 'covid19_tweets_with_sentiment.csv' 파일을 확인해보세요.")