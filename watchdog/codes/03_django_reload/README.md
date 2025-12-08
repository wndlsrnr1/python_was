# Django 자동 리로드 예제

## 실행 방법

### 1. Django 프로젝트 생성

```bash
django-admin startproject myproject
cd myproject
```

### 2. 개발 서버 실행

```bash
python manage.py runserver
```

### 3. 파일 변경 테스트

다른 터미널에서 파일을 수정해보세요:

```bash
# views.py 수정
echo "# 변경사항" >> myapp/views.py
```

서버가 자동으로 재시작되는 것을 확인할 수 있습니다.

## 자동 리로드 확인

서버 로그에서 다음과 같은 메시지를 볼 수 있습니다:

```
Watching for file changes with StatReloader
```

파일을 변경하면:

```
/Users/.../myapp/views.py changed, reloading
```

## 주의사항

- 프로덕션 환경에서는 `runserver`를 사용하지 마세요
- 자동 리로드는 개발 환경에서만 사용하세요

