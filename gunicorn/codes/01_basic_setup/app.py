def application(environ, start_response):
    """최소한의 WSGI 애플리케이션"""
    status = "200 OK"
    headers = [
        ("Content-Type", "text/html; charset=utf-8"),
    ]
    start_response(status, headers)

    # 요청 정보 출력
    method = environ.get("REQUEST_METHOD", "GET")
    path = environ.get("PATH_INFO", "/")

    body = f"""
    <html>
    <head><title>Gunicorn 테스트</title></head>
    <body>
        <h1>Gunicorn이 정상 작동합니다!</h1>
        <p>요청 메서드: {method}</p>
        <p>요청 경로: {path}</p>
    </body>
    </html>
    """.encode(
        "utf-8"
    )

    return [body]
