# 핸들러 예제

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

### 3. 커스텀 핸들러 실행

```bash
python -c "
import time
from watchdog.observers import Observer
from custom_handler import LoggingHandler

handler = LoggingHandler()
observer = Observer()
observer.schedule(handler, '.', recursive=False)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
"
```

### 4. 필터링 핸들러 실행

```bash
python -c "
import time
from watchdog.observers import Observer
from filtered_handler import PythonFileHandler

handler = PythonFileHandler()
observer = Observer()
observer.schedule(handler, '.', recursive=False)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
"
```

## 예제 설명

- `custom_handler.py`: 파일 변경을 로그 파일에 기록하는 핸들러
- `filtered_handler.py`: Python 파일만 감시하는 핸들러

## 테스트

다른 터미널에서 파일을 생성/수정해보세요:

```bash
# Python 파일 생성
echo "print('hello')" > test.py

# Python 파일 수정
echo "print('world')" >> test.py

# 다른 파일 생성 (감지되지 않음)
echo "content" > test.txt
```

