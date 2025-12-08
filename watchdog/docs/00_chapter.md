# Watchdog 교과서: Python 파일 모니터링 완전 정복

> **대상 독자**: Spring/Tomcat 경험자  
> **학습 목표**: Django/FastAPI에서 파일 모니터링과 자동 리로드가 어떻게 동작하는지 완전히 이해하기  
> **학습 방식**: 이론 → 실습 → 심화 순서로 따라하며 학습

---

## 📚 목차 및 학습 로드맵

### 전체 구조

```
00_chapter.md (이 파일) - 목차 및 학습 가이드
    ↓
01_overview.md - 개요 및 왜 필요한가
    ↓
02_file_events.md - 파일 시스템 이벤트 이해
    ↓
03_basic_setup.md - 기본 설치 및 사용
    ↓
04_observer_pattern.md - 옵저버 패턴 및 핸들러 이해
    ↓
05_auto_reload.md - Django/FastAPI 자동 리로드 활용
    ↓
06_advanced_usage.md - 고급 사용법
    ↓
07_comparison.md - 다른 도구와의 비교 정리
```

### 파일별 학습 목표

| 파일 | 학습 목표 | 예상 시간 |
|------|----------|----------|
| **01_overview.md** | watchdog이 무엇인지, 왜 필요한지 직관적 이해 | 15분 |
| **02_file_events.md** | 파일 시스템 이벤트의 종류와 동작 방식 이해 | 20분 |
| **03_basic_setup.md** | 실제로 설치하고 기본 사용법 습득 | 25분 |
| **04_observer_pattern.md** | 옵저버 패턴과 핸들러의 동작 원리 이해 | 30분 |
| **05_auto_reload.md** | Django/FastAPI에서 자동 리로드가 어떻게 동작하는지 | 30분 |
| **06_advanced_usage.md** | 필터링, 디바운싱 등 고급 기능 습득 | 25분 |
| **07_comparison.md** | 다른 도구와의 비교를 통한 통합적 이해 | 15분 |

**총 예상 학습 시간**: 약 2.5시간

### 학습 순서 가이드

#### 초보자를 위한 추천 순서

1. **01_overview.md** - 먼저 읽어서 전체 그림 파악
2. **03_basic_setup.md** - 바로 실습해보며 감 잡기
3. **02_file_events.md** - 원리 이해하기
4. **04_observer_pattern.md** - 핸들러 작성하기
5. **05_auto_reload.md** - Django/FastAPI에서 실제 사용
6. **06_advanced_usage.md** - 심화 학습
7. **07_comparison.md** - 전체 정리

#### 빠른 실습을 원하는 경우

1. **01_overview.md** - 간단히 읽기
2. **03_basic_setup.md** - 바로 실습
3. **05_auto_reload.md** - Django/FastAPI 자동 리로드 이해
4. 필요시 다른 파일 참조

### 예제 코드 위치

모든 실습 예제 코드는 `watchdog/codes/` 디렉토리에 있습니다:

```
watchdog/codes/
├── 01_basic_setup/        # 기본 파일 모니터링 예제
├── 02_handler_example/    # 핸들러 예제
├── 03_django_reload/      # Django 자동 리로드 예제
├── 04_fastapi_reload/     # FastAPI 자동 리로드 예제
└── 05_advanced_example/   # 고급 사용법 예제
```

각 예제 디렉토리에는 `README.md` 파일이 포함되어 있어 실행 방법을 확인할 수 있습니다.

### Spring/Tomcat 경험자를 위한 가이드

이 교과서는 Spring/Tomcat 경험자를 대상으로 작성되었습니다. 각 챕터에서 다음과 같은 비교를 제공합니다:

- **Spring의 파일 감시**: Java의 WatchService와 비교
- **리스너 패턴**: Spring의 이벤트 리스너와 비교
- **자동 리로드**: Spring Boot DevTools와 비교

### Django/FastAPI와의 관계

Watchdog은 Django와 FastAPI의 자동 리로드 기능의 핵심입니다:

- **Django**: `python manage.py runserver`의 자동 리로드
- **FastAPI/Uvicorn**: `uvicorn main:app --reload` 옵션
- **내부 구현**: 모두 watchdog을 사용하여 파일 변경 감지

### 다음 단계

1. **01_overview.md**부터 시작하세요
2. 각 파일을 순서대로 읽으며 실습하세요
3. 궁금한 점이 있으면 해당 파일을 다시 참조하세요

---

## 참고 자료

- [Watchdog 공식 문서](https://python-watchdog.readthedocs.io/)
- [Django 자동 리로드 문서](https://docs.djangoproject.com/en/stable/ref/django-admin/#runserver)
- [Uvicorn 리로드 문서](https://www.uvicorn.org/settings/#reload)

---

**이제 01_overview.md부터 시작하세요!**

