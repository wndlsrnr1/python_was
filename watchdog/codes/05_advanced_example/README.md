# 고급 사용법 예제

## 실행 방법

### 1. 가상환경 생성 및 활성화 (선택사항)

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Watchdog 설치

```bash
pip install watchdog
```

### 3. 디바운싱 핸들러 실행

```bash
python debounced_handler.py
```

## 예제 설명

- `debounced_handler.py`: 디바운싱을 사용하여 연속된 이벤트를 한 번만 처리하는 핸들러

## 테스트

다른 터미널에서 파일을 빠르게 여러 번 수정해보세요:

```bash
# 빠르게 여러 번 수정
echo "1" >> test.txt
echo "2" >> test.txt
echo "3" >> test.txt
```

디바운싱 핸들러는 1초 후에 한 번만 이벤트를 처리합니다.

