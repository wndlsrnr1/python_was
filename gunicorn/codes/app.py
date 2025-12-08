"""
Gunicorn은 정적 파일을 직접 서빙하지 않습니다. 다음 중 하나를 사용

Nginx/Apache: 리버스 프록시로 정적 파일 서빙
WhiteNoise: Django 미들웨어로 정적 파일 서빙

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware", # 추가
]

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# 빌드
mvn clean package

# 실행
java -jar target/myapp.jar

Spring Boot: JAR 파일로 패키징 하여 실행
Django: 소스코드를 직접 실행

03_django_example/
    manage.py
    mypporejct/
        __init__.py
        setting .py
        urls.py
        wsgi.py
    myapp.py
        __init__.py
        views.py
        urls.py

실행

cd gunicorn/codes/... 

이제 Djanog 에서 Gunicorn을 사용하는 방법을 배웠습니다. 다음 단계
.. fast api .md FastAPI에서 aSGI 서버 사용법 이해
config.md 프로덕션 환경을 위한 고급 설정 방법 습득


"""