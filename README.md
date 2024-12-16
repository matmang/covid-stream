# Overview

이 프로젝트는 covid19_tweets.csv 데이터를 실시간 스트리밍 환경(Kafka)에서 처리하고, 감성 분석(Sentiment Analysis)을 통해 트윗의 감정 분포 변화를 관찰하는 실험을 다룹니다. 또한, 일반적인 전체 데이터 처리와 비교하여 **Reservoir Sampling** 과 **Count-Min Sketch(CMS)** 를 활용한 근사 추정 방법의 결과를 비교합니다.

## Components
- Producer (producer.py):
covid19_tweets.csv 파일을 읽어 Kafka 토픽(covid_tweets_topic)에 데이터 레코드를 전송합니다. 스트리밍 환경을 모사하기 위해 메시지를 순차적으로 보내는 역할을 담당합니다.
- Reservoir Consumer (reservoir-consumer.py):
Kafka로부터 스트림 데이터를 소비하며, Reservoir Sampling 기법을 적용합니다. 약 10,000개의 랜덤 샘플을 유지한 뒤, 해당 샘플에 대해 감성 분석을 수행하고 결과를 CSV로 저장합니다.
- Count-Min Sketch Consumer (countmin-consumer.py):
Kafka로부터 스트림 데이터를 소비하며, Count-Min Sketch를 통해 감성 레이블(positive, neutral, negative)의 빈도를 근사적으로 추정합니다. 모든 데이터를 처리하되 CMS를 이용하여 빈도를 효율적으로 추정하고, 최종 추정치를 CSV로 저장합니다.

Files and Directories
- producer.py: Kafka Producer 코드
- reservoir-consumer.py: Reservoir Sampling 기반 감성 분석 코드
- countmin-consumer.py: Count-Min Sketch 기반 감성 분석 코드
- covid19_tweets.csv: 원본 트윗 데이터 (별도 제공)
- reservoir_sentiment_results.csv: Reservoir Sampling 결과 파일
- cms_sentiment_results.csv: Count-Min Sketch 결과 파일
- images/: 실험 결과를 나타내는 그래프나 시각자료 폴더

How to Run
1. Kafka & Zookeeper 실행
사전에 Kafka와 Zookeeper가 구동 중이어야 합니다.
2. 토픽 생성 (옵션)
```bash
kafka-topics.sh --create --topic covid_tweets_topic --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1\
```


3. Producer 실행
```bash
python producer.py
```
producer.py 실행 후, covid19_tweets_topic 토픽에 메시지가 전송됩니다.

4. Reservoir Consumer 실행
```bash
python reservoir-consumer.py
```
consumer 종료 후 reservoir_sentiment_results.csv가 생성됩니다.

5. Count-Min Sketch Consumer 실행
```bash
python countmin-consumer.py
```
consumer 종료 후 cms_sentiment_results.csv가 생성됩니다.

Experimental Setup
- 데이터셋: covid19_tweets.csv (약 179,113개 트윗)
- 감성 분석 모델: cardiffnlp/twitter-roberta-base-sentiment-latest (Hugging Face Transformers 사용)
- Sampling Size: Reservoir Sampling은 10,000개 샘플 유지
- Count-Min Sketch: width=1000, depth=5 (또는 width=100)

Results
1. 전체 데이터셋 감성분석 비율 (총 179,113개 트윗 대상)
![whole](/images/whole_dataset.png)

| Sentiment | Ratio (%)   |
|-----------|-------------|
| neutral   | 52.843863   |
| negative  | 34.412775   |
| positive  | 12.743363   |


2. Reservoir Sampling 감성분석 비율 (10,000개 샘플)
![whole](/images/reservoir.png)

| Sentiment | Ratio (%) |
|-----------|-----------|
| neutral   | 50.33     |
| negative  | 38.41     |
| positive  | 11.26     |


3. Count-Min Sketch 감성분석 비율 (width=1000 가정)
![whole](/images/whole_dataset.png)

| Sentiment | Ratio (%)   |
|-----------|-------------|
| neutral   | 52.843536   |
| negative  | 34.413315   |
| positive  | 12.743149   |



Interpretation
- Reservoir Sampling 결과:
Reservoir Sampling은 임의의 10,000개 샘플을 추출한 결과, 원본 비율(특히 중립 감성 비율)에 비해 약간의 편차가 발생했습니다. 이는 샘플링 과정에서 일부 감정 레이블이 과소 혹은 과대 대표될 수 있기 때문입니다.
- Count-Min Sketch 결과:
Count-Min Sketch는 근사적으로 빈도를 추정한 결과 원본 비율과 거의 유사한 수치를 보여주었습니다. 이는 CMS가 대규모 데이터에서 빈도를 근사하는데 충분히 유용함을 시사합니다.

Conclusion
- 전체 데이터 감성분석: 정확한 비율 파악 가능하지만 시간/자원 소모 큼.
- Reservoir Sampling: 자원 절약과 데이터 접근성 향상, 그러나 정확도 손실 발생.
- Count-Min Sketch: 근사 빈도 추정을 통해 원본에 매우 가까운 분포 파악이 가능하며, 메모리 사용 효율성을 개선.

이 실험을 통해 스트리밍 환경에서 대규모 데이터를 효율적으로 처리하고, 감성 분석 결과를 근사하는 다양한 접근법의 장단점을 살펴볼 수 있었습니다.
