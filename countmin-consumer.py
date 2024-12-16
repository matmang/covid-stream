from kafka import KafkaConsumer
import json
import pandas as pd
import signal
import mmh3
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

class CountMinSketch:
    def __init__(self, width=1000, depth=5, seed=12345):
        self.width = width
        self.depth = depth
        self.seed = seed
        self.table = [[0] * width for _ in range(depth)]

    def _hash(self, item, i):
        return mmh3.hash(item, self.seed + i) % self.width

    def add(self, item, count=1):
        item = str(item)
        for i in range(self.depth):
            index = self._hash(item, i)
            self.table[i][index] += count

    def estimate(self, item):
        item = str(item)
        return min(self.table[i][self._hash(item, i)] for i in range(self.depth))

# 안전한 종료를 위해 시그널 핸들러 추가
stop_flag = False
def signal_handler(sig, frame):
    global stop_flag
    stop_flag = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# 모델 및 파이프라인 로드
model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
sentiment_pipe = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

# 감성 분석 함수 정의
def get_sentiment(text):
    result = sentiment_pipe(text[:512])  # 512 토큰 이내로 잘라냄
    return result[0]['label']

# Count-Min Sketch 초기화
cms = CountMinSketch(width=100, depth=5)

consumer = KafkaConsumer(
    'covid_tweets_topic',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
    consumer_timeout_ms=5000  # 5초 동안 메시지가 없으면 종료
)

# 감성 레이블 목록 (모델 출력 기준)
sentiments_list = ['positive', 'neutral', 'negative']

# Kafka 메시지 소비 및 Count-Min Sketch 업데이트
for message in consumer:
    if stop_flag:
        break

    tweet_data = message.value
    text = tweet_data.get('text', '')
    
    # 감성 분석
    sentiment = get_sentiment(text)
    print(f"Sentiment: {sentiment}")
    cms.add(sentiment)

# 최종적으로 Count-Min Sketch에서 추정한 결과 저장
final_estimates = {sentiment: cms.estimate(sentiment) for sentiment in sentiments_list}

# 결과를 DataFrame으로 변환 및 저장
df = pd.DataFrame([final_estimates])
df.to_csv('cms_sentiment_results.csv', index=False)

print(f"Count-Min Sketch 완료. 최종 추정치가 cms_sentiment_results.csv에 저장되었습니다.")