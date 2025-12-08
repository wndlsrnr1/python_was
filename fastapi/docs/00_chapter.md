# FastAPI 교과서: Python 웹 프레임워크 완전 정복

> **대상 독자**: Spring/Tomcat 경험자  
> **학습 목표**: FastAPI가 어떻게 돌아가는지, 어떻게 실행하는지, 기본 원리를 완전히 이해하기  
> **학습 방식**: 이론 → 실습 → 심화 순서로 따라하며 학습

---

## 📚 목차 및 학습 로드맵

### 전체 구조

```
00_chapter.md (이 파일) - 목차 및 학습 가이드
    ↓
01_overview.md - FastAPI 개요 및 왜 필요한가
    ↓
02_basic_setup.md - 기본 설치 및 실행
    ↓
03_asgi_protocol.md - ASGI 프로토콜 이해
    ↓
04_architecture.md - FastAPI 아키텍처 및 동작 원리
    ↓
05_routing.md - 라우팅 및 엔드포인트 작성
    ↓
06_uvicorn_gunicorn.md - uvicorn과 gunicorn 이해
    ↓
07_production.md - 프로덕션 배포 기본
    ↓
08_comparison.md - Spring과의 종합 비교 정리
```

### 파일별 학습 목표

| 파일 | 학습 목표 | 예상 시간 |
|------|----------|----------|
| **01_overview.md** | FastAPI가 무엇인지, Spring과 어떤 차이가 있는지 직관적 이해 | 20분 |
| **02_basic_setup.md** | 실제로 설치하고 실행해보며 기본 사용법 습득 | 25분 |
| **03_asgi_protocol.md** | ASGI 프로토콜을 통한 애플리케이션-서버 통신 방식 이해 | 20분 |
| **04_architecture.md** | FastAPI 내부 동작 원리와 요청 처리 흐름 이해 | 30분 |
| **05_routing.md** | 실제 API 엔드포인트를 작성하는 방법 습득 | 30분 |
| **06_uvicorn_gunicorn.md** | FastAPI를 실행하는 서버의 역할과 사용법 이해 | 25분 |
| **07_production.md** | 실제 운영 환경에서 FastAPI를 배포하는 기본 방법 습득 | 25분 |
| **08_comparison.md** | Spring Boot와 FastAPI 전반 비교를 통한 통합적 이해 | 20분 |

**총 예상 학습 시간**: 약 3시간

### 학습 순서 가이드

#### 초보자를 위한 추천 순서

1. **01_overview.md** - 먼저 읽어서 전체 그림 파악
2. **02_basic_setup.md** - 바로 실습해보며 감 잡기
3. **03_asgi_protocol.md** - 원리 이해하기
4. **04_architecture.md** - FastAPI 내부 구조 이해
5. **05_routing.md** - 실제 API 개발 시작
6. **06_uvicorn_gunicorn.md** - 서버 이해하기
7. **07_production.md** - 프로덕션 배포 준비
8. **08_comparison.md** - 전체 정리

#### 빠른 실습을 원하는 경우

1. **01_overview.md** - 간단히 읽기
2. **02_basic_setup.md** - 바로 실습
3. **05_routing.md** - API 개발 시작
4. **06_uvicorn_gunicorn.md** - 서버 설정
5. 필요시 다른 파일 참조

### 예제 코드 위치

모든 실습 예제 코드는 `fastapi/codes/` 디렉토리에 있습니다:

```
fastapi/codes/
├── 01_basic_setup/         # 기본 설치 및 실행 예제
├── 02_architecture_demo/   # 아키텍처 시각화 예제
├── 03_routing_example/     # 라우팅 예제 프로젝트
├── 04_server_setup/        # 서버 설정 예제
└── 05_production_example/   # 프로덕션 설정 예제
```

각 예제 디렉토리에는 `README.md` 파일이 포함되어 있어 실행 방법을 확인할 수 있습니다.

### Spring/Tomcat 경험자를 위한 가이드

이 교과서는 Spring/Tomcat 경험자를 대상으로 작성되었습니다. 각 챕터에서 다음과 같은 비교를 제공합니다:

- **Spring Boot vs FastAPI**: 웹 프레임워크 아키텍처 비교
- **Tomcat vs Uvicorn/Gunicorn**: 서버 역할과 아키텍처 비교
- **@RestController vs FastAPI Router**: API 엔드포인트 작성 방식 비교
- **Spring DI vs FastAPI Dependency Injection**: 의존성 주입 시스템 비교
- **WAR 배포 vs Python 모듈**: 배포 방식 비교

### uvicorn과 gunicorn의 관계

FastAPI를 실행하려면 ASGI 서버가 필요합니다:

- **Uvicorn**: ASGI 서버 (개발 및 단순 프로덕션 환경)
- **Gunicorn + Uvicorn 워커**: 프로덕션 환경에서 권장되는 조합
- **06_uvicorn_gunicorn.md**에서 이 조합에 대해 자세히 다룹니다

### 다음 단계

1. **01_overview.md**부터 시작하세요
2. 각 파일을 순서대로 읽으며 실습하세요
3. 궁금한 점이 있으면 해당 파일을 다시 참조하세요

---

## 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [ASGI 스펙](https://asgi.readthedocs.io/)
- [Uvicorn 공식 문서](https://www.uvicorn.org/)
- [Gunicorn 공식 문서](https://gunicorn.org/)

---

**이제 01_overview.md부터 시작하세요!**

