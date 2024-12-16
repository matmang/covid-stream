from kafka import KafkaConsumer
import json
import pandas as pd
import signal
import random
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from tqdm import tqdm

class ReservoirSampler:
    def __init__(self, size):
        self.size = size
        self.sample = []
        self.count = 0  # 들어온 데이터 개수

    def add(self, element):
        if len(self.sample) < self.size:
            self.count += 1
            # 샘플이 아직 가득 차지 않으면 그대로 추가
            self.sample.append(element)
        else:
            # 이미 가득 찬 경우, 1~size 범위에서 랜덤 인덱스 선택
            r = random.randint(1, self.size)
            if r <= self.size:
                self.sample[r-1] = element  # 해당 위치 교체

    def get_sample(self):
        return self.sample


# 안전한 종료를 위해 시그널 핸들러 추가
stop_flag = False
def signal_handler(sig, frame):
    global stop_flag
    stop_flag = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# 1. 모델 및 파이프라인 로드
model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
sentiment_pipe = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

# 2. 감성 분석 함수 정의
def get_sentiment(text):
    result = sentiment_pipe(text[:512])  # 512토큰 이내로 잘라내기
    return result[0]['label']

# 3. Reservoir Sampler 초기화
reservoir_size = 10000
sampler = ReservoirSampler(size=reservoir_size)

consumer = KafkaConsumer(
    'covid_tweets_topic',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
    consumer_timeout_ms=5000  # 5초 동안 메시지가 없으면 종료
)

# 4. Kafka 메시지 소비 및 Reservoir Sampling 수행
for message in consumer:
    if stop_flag:
        break
    
    tweet_data = message.value
    text = tweet_data.get('text', '')
    
    # Reservoir Sampling 수행
    sampler.add(text)
    print("Reservoir Sampling:", sampler.count)

print("Reservoir Sampling 완료. 최종 샘플 수:", len(sampler.get_sample()))

# 5. 최종 Reservoir 샘플에 대해 감성 분석 수행
sampled_texts = sampler.get_sample()
sentiments = [get_sentiment(text) for text in tqdm(sampled_texts, desc="Sentiment Analysis")]

# 6. 결과 저장
df = pd.DataFrame(sentiments, columns=['sentiment'])
df.to_csv('reservoir_sentiment_results.csv', index=False)

print(f"Reservoir Sampling 완료. 총 {len(sampled_texts)}개의 샘플이 저장되었습니다.")