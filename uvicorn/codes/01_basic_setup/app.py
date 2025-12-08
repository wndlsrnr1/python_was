async def application(scope, receive, send):
    """최소한의 ASGI 애플리케이션"""
    if scope["type"] != "http":
        return

    # 요청 정보 추출
    method = scope.get("method", "GET")
    path = scope.get("path", "/")

    # 응답 생성
    body = f"""
    <html>
    <head><title>Uvicorn 테스트</title></head>
    <body>
        <h1>Uvicorn이 정상 작동합니다!</h1>
        <p>요청 메서드: {method}</p>
        <p>요청 경로: {path}</p>
    </body>
    </html>
    """.encode(
        "utf-8"
    )

    # 응답 전송
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"text/html; charset=utf-8"]],
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": body,
        }
    )
