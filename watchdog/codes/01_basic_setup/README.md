# 기본 파일 모니터링 예제

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

### 3. 기본 모니터링 실행

```bash
python watch.py
```

### 4. 재귀적 모니터링 실행

```bash
python watch_recursive.py
```

## 테스트 방법

다른 터미널에서 파일을 생성/수정/삭제해보세요:

```bash
# 파일 생성
touch test.txt

# 파일 수정
echo "content" >> test.txt

# 파일 삭제
rm test.txt

# 파일 이름 변경
mv test.txt new_test.txt
```

실행 중인 터미널에서 이벤트가 출력되는 것을 확인할 수 있습니다.

## 차이점

- `watch.py`: 현재 디렉토리만 모니터링 (`recursive=False`)
- `watch_recursive.py`: 하위 디렉토리까지 모니터링 (`recursive=True`)

