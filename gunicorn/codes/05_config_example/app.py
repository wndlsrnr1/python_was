def application(environ, start_response):
    """설정 파일 테스트용 WSGI 애플리케이션"""
    status = '200 OK'
    headers = [
        ('Content-Type', 'text/html; charset=utf-8'),
    ]
    start_response(status, headers)
    
    body = """
    <html>
    <head><title>Gunicorn 설정 파일 테스트</title></head>
    <body>
        <h1>Gunicorn 설정 파일이 정상 작동합니다!</h1>
        <p>이 페이지는 gunicorn.conf.py 설정 파일을 사용하여 실행되었습니다.</p>
    </body>
    </html>
    """.encode('utf-8')
    
    return [body]

