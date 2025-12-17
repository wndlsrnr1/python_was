# Channel 패턴 교과서: Adapter와 Channel의 정확한 이해

> **대상 독자**: Spring/Tomcat 경험자, Python 비동기 프로그래밍 학습자  
> **학습 목표**: Adapter와 Channel의 본질적 차이를 이해하고, 배치/스트리밍 변환과 블로킹/비동기 실행 모델을 정확히 구분하기  
> **학습 방식**: 이론 → 실습 → 심화 순서로 따라하며 학습

---

## 📚 목차 및 학습 로드맵

### 전체 구조

```
00_chapter.md (이 파일) - 목차 및 학습 가이드
    ↓
01_overview.md - 개요 및 핵심 개념 (Adapter vs Channel)
    ↓
02_batch_vs_streaming.md - 배치 변환과 스트리밍 변환
    ↓
03_blocking_vs_async.md - 블로킹과 비동기 실행 모델
    ↓
04_adapter_pattern.md - Adapter 패턴 상세
    ↓
05_channel_pattern.md - Channel 패턴 상세
    ↓
06_pipeline_pattern.md - Pipeline 패턴 (여러 Channel 연결)
    ↓
07_naming_conventions.md - 네이밍 규칙 및 용어 정리
    ↓
08_practical_example.md - 실전 예제: 오디오 STT 파이프라인
```

### 파일별 학습 목표

| 파일 | 학습 목표 | 예상 시간 |
|------|----------|----------|
| **01_overview.md** | Adapter와 Channel의 본질적 차이를 직관적으로 이해 | 20분 |
| **02_batch_vs_streaming.md** | 배치 변환과 스트리밍 변환의 차이를 명확히 구분 | 25분 |
| **03_blocking_vs_async.md** | 블로킹과 비동기 실행 모델의 차이 이해 | 25분 |
| **04_adapter_pattern.md** | Adapter 패턴 구현과 사용법을 실습으로 학습 | 30분 |
| **05_channel_pattern.md** | Channel 패턴 구현과 사용법을 실습으로 학습 | 30분 |
| **06_pipeline_pattern.md** | 여러 Channel을 연결하는 Pipeline 패턴 학습 | 35분 |
| **07_naming_conventions.md** | 정확한 용어 사용과 네이밍 규칙 정리 | 20분 |
| **08_practical_example.md** | 실제 프로젝트에서 사용하는 전체 예제 | 40분 |

**총 예상 학습 시간**: 약 3시간

### 학습 순서 가이드

#### 초보자를 위한 추천 순서

1. **01_overview.md** - 먼저 읽어서 전체 그림 파악
2. **02_batch_vs_streaming.md** - 배치와 스트리밍의 차이 이해
3. **03_blocking_vs_async.md** - 실행 모델의 차이 이해
4. **04_adapter_pattern.md** - Adapter 패턴 실습
5. **05_channel_pattern.md** - Channel 패턴 실습
6. **06_pipeline_pattern.md** - Pipeline 패턴 실습
7. **07_naming_conventions.md** - 용어 정리
8. **08_practical_example.md** - 실전 예제로 통합 이해

#### 빠른 실습을 원하는 경우

1. **01_overview.md** - 핵심 개념만 읽기
2. **02_batch_vs_streaming.md** - 배치/스트리밍 차이 이해
3. **05_channel_pattern.md** - Channel 패턴 바로 실습
4. **08_practical_example.md** - 실전 예제로 학습
5. 필요시 다른 파일 참조

### 예제 코드 위치

모든 실습 예제 코드는 `realtimestt/codes/channel_patterns/` 디렉토리에 있습니다:

```
realtimestt/codes/channel_patterns/
├── transcription/
│   ├── channels/          # Channel 구현 예제
│   │   ├── audio_channels.py
│   │   ├── grpc_channels.py
│   │   ├── result_channels.py
│   │   └── websocket_channels.py
│   ├── services/          # Pipeline 구현 예제
│   │   └── realtime_stt_pipeline.py
│   └── consumers/         # Consumer 구현 예제
│       └── realtime_stt_consumer.py
└── examples/              # 간단한 예제 코드
    ├── adapter_example.py
    ├── channel_example.py
    └── pipeline_example.py
```

각 예제에는 주석과 설명이 포함되어 있어 따라치며 학습할 수 있습니다.

### Spring/Tomcat 경험자를 위한 가이드

이 교과서는 Spring/Tomcat 경험자를 대상으로 작성되었습니다. 각 챕터에서 다음과 같은 비교를 제공합니다:

- **Spring Converter vs Adapter**: 형식 변환 패턴 비교
- **Spring Stream vs Channel**: 스트리밍 처리 패턴 비교
- **동기 처리 vs 비동기 처리**: 실행 모델 비교
- **배치 작업 vs 스트리밍 작업**: 처리 단위 비교

### 핵심 개념 미리보기

이 교과서에서 다루는 핵심 개념:

1. **Adapter 패턴**: 인터페이스/형식 변환 (동기/비동기 모두 가능)
2. **Channel 패턴**: 스트리밍/파이프라인 (동기/비동기 모두 가능)
3. **배치 변환**: 전체 입력 → 전체 출력
4. **스트리밍 변환**: 청크 입력 → 청크 출력
5. **블로킹**: 호출자가 완료까지 대기
6. **비동기**: 처리 중에도 다른 작업 가능

**중요**: "동기=Adapter / 비동기=Channel"이라는 1:1 매핑은 **잘못된 이해**입니다. 정확한 구분은 **배치 vs 스트리밍**입니다.

### 다음 단계

1. **01_overview.md**부터 시작하세요
2. 각 파일을 순서대로 읽으며 실습하세요
3. 예제 코드를 따라치며 실행해보세요
4. 궁금한 점이 있으면 해당 파일을 다시 참조하세요

---

## 참고 자료

- [GoF Adapter 패턴](https://en.wikipedia.org/wiki/Adapter_pattern)
- [CSP (Communicating Sequential Processes)](https://en.wikipedia.org/wiki/Communicating_sequential_processes)
- [Python asyncio 공식 문서](https://docs.python.org/3/library/asyncio.html)
- [Django Channels 문서](https://channels.readthedocs.io/)

---

**이제 01_overview.md부터 시작하세요!**

