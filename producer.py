import csv
import time
from kafka import KafkaProducer
import json

# Kafka Producer 설정
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# CSV 파일 읽기
csv_file = 'covid19_tweets.csv'
topic_name = 'covid_tweets_topic'

with open(csv_file, mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    
    for row in reader:
        # 필요한 컬럼만 선택 (선택적으로 필터링 가능)
        record = {
            "user_name": row["user_name"],
            "user_location": row["user_location"],
            "text": row["text"],
            "hashtags": row["hashtags"],
            "date": row["date"]
        }
        # Kafka로 메시지 전송
        producer.send(topic_name, value=record)
        print(f"Sent: {record}")
        
        # 약간의 지연을 추가해 스트리밍처럼 보이게 설정 (선택적)

# 프로듀서 닫기
producer.close()