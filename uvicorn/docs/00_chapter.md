# Uvicorn 교과서: Python ASGI 서버 완전 정복

> **대상 독자**: Spring/Tomcat 경험자  
> **학습 목표**: Django/FastAPI에서 uvicorn을 사용하는 방법과 동작 원리를 완전히 이해하기  
> **학습 방식**: 이론 → 실습 → 심화 순서로 따라하며 학습

---

## 📚 목차 및 학습 로드맵

### 전체 구조

```
00_chapter.md (이 파일) - 목차 및 학습 가이드
    ↓
01_overview.md - 개요 및 왜 필요한가
    ↓
02_asgi_protocol.md - ASGI 프로토콜 이해
    ↓
03_basic_setup.md - 기본 설치 및 실행
    ↓
04_architecture.md - 아키텍처 및 동작 원리
    ↓
05_fastapi.md - FastAPI에서 사용하기
    ↓
06_django.md - Django에서 사용하기
    ↓
07_config.md - 설정 파일 및 고급 옵션
    ↓
08_comparison.md - Gunicorn/Spring과의 비교 정리
```

### 파일별 학습 목표

| 파일 | 학습 목표 | 예상 시간 |
|------|----------|----------|
| **01_overview.md** | uvicorn이 무엇인지, 왜 필요한지 직관적 이해 | 15분 |
| **02_asgi_protocol.md** | ASGI 프로토콜을 통한 애플리케이션-서버 통신 방식 이해 | 20분 |
| **03_basic_setup.md** | 실제로 설치하고 실행해보며 기본 사용법 습득 | 20분 |
| **04_architecture.md** | 이벤트 루프와 비동기 처리 원리 이해 | 30분 |
| **05_fastapi.md** | FastAPI 프로젝트에서 실전 적용 | 25분 |
| **06_django.md** | Django에서 ASGI 모드로 사용하기 | 25분 |
| **07_config.md** | 프로덕션 환경을 위한 고급 설정 방법 습득 | 20분 |
| **08_comparison.md** | Gunicorn/Spring과의 비교를 통한 통합적 이해 | 15분 |

**총 예상 학습 시간**: 약 2.5시간

### 학습 순서 가이드

#### 초보자를 위한 추천 순서

1. **01_overview.md** - 먼저 읽어서 전체 그림 파악
2. **03_basic_setup.md** - 바로 실습해보며 감 잡기
3. **02_asgi_protocol.md** - 원리 이해하기
4. **05_fastapi.md** - FastAPI 사용자라면 이 파일부터
5. **06_django.md** - Django 사용자라면 이 파일부터
6. **04_architecture.md** - 심화 학습
7. **07_config.md** - 프로덕션 배포 준비
8. **08_comparison.md** - 전체 정리

#### 빠른 실습을 원하는 경우

1. **01_overview.md** - 간단히 읽기
2. **03_basic_setup.md** - 바로 실습
3. **05_fastapi.md** 또는 **06_django.md** - 자신의 프레임워크에 맞춰 실습
4. 필요시 다른 파일 참조

### 예제 코드 위치

모든 실습 예제 코드는 `uvicorn/codes/` 디렉토리에 있습니다:

```
uvicorn/codes/
├── 01_basic_setup/      # 기본 설치 및 실행 예제
├── 02_async_demo/       # 비동기 동작 시각화 예제
├── 03_fastapi_example/  # FastAPI 예제 프로젝트
├── 04_django_example/   # Django ASGI 예제 프로젝트
└── 05_config_example/   # 설정 파일 예제
```

각 예제 디렉토리에는 `README.md` 파일이 포함되어 있어 실행 방법을 확인할 수 있습니다.

### Spring/Tomcat 경험자를 위한 가이드

이 교과서는 Spring/Tomcat 경험자를 대상으로 작성되었습니다. 각 챕터에서 다음과 같은 비교를 제공합니다:

- **Tomcat vs Uvicorn**: 서버 역할과 아키텍처 비교
- **스레드 모델 vs 이벤트 루프**: 동시성 처리 방식 비교
- **서블릿 스펙 vs ASGI**: 프로토콜 비교
- **WAR 배포 vs Python 모듈**: 배포 방식 비교

### Gunicorn과의 관계

Uvicorn은 **ASGI 서버**이고, Gunicorn은 **WSGI 서버**입니다. 하지만:

- **Gunicorn + Uvicorn 워커**: Gunicorn이 uvicorn 워커를 사용하여 ASGI 애플리케이션 실행 가능
- **07_config.md**에서 이 조합에 대해 자세히 다룹니다

### 다음 단계

1. **01_overview.md**부터 시작하세요
2. 각 파일을 순서대로 읽으며 실습하세요
3. 궁금한 점이 있으면 해당 파일을 다시 참조하세요

---

## 참고 자료

- [Uvicorn 공식 문서](https://www.uvicorn.org/)
- [ASGI 스펙](https://asgi.readthedocs.io/)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Django ASGI 문서](https://docs.djangoproject.com/en/stable/howto/deployment/asgi/)

---

**이제 01_overview.md부터 시작하세요!**

