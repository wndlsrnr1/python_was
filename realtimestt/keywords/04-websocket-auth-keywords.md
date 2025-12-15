# WebSocket 및 인증 관련 키워드

## WebSocket 통신

### WebSocket만의 인증 문제
WebSocket은 HTTP와 달리 연결이 지속되므로, 연결 시점에 한 번만 인증하는 것이 일반적입니다. 연결 후 인증 토큰이 만료되거나 변경되는 경우를 처리해야 합니다.

### ConsumerPattern
Django Channels에서 WebSocket 연결을 처리하는 패턴입니다. Consumer 클래스를 상속받아 `connect()`, `disconnect()`, `receive()` 메서드를 구현하여 WebSocket 이벤트를 처리합니다.

### connect
WebSocket 연결이 수립될 때 호출되는 메서드입니다. 인증 검증, 초기 설정 등을 수행합니다.

### disconnect
WebSocket 연결이 종료될 때 호출되는 메서드입니다. 리소스 정리, 세션 종료 등을 수행합니다.

### receive
클라이언트로부터 메시지를 받을 때 호출되는 메서드입니다. 메시지 타입에 따라 적절한 처리 로직을 실행합니다.

### sessionContext pattern
WebSocket 연결마다 세션 컨텍스트를 유지하는 패턴입니다. 연결 상태, 사용자 정보, 처리 중인 작업 등을 저장하고 관리합니다. 각 연결의 생명주기 동안 상태를 유지하는 데 사용됩니다.

## JWT (JSON Web Token)

### jwt.header
JWT의 첫 번째 부분입니다. 토큰 타입(JWT)과 서명 알고리즘(예: HS256, RS256)을 포함합니다. Base64Url로 인코딩되어 있습니다.

### payload
JWT의 두 번째 부분입니다. 클레임(claim) 정보를 포함합니다. 사용자 ID, 권한, 만료 시간 등의 정보가 담깁니다. Base64Url로 인코딩되어 있습니다.

### jwt.signature
JWT의 세 번째 부분입니다. 헤더와 페이로드를 비밀키로 서명한 값입니다. 토큰의 무결성을 검증하는 데 사용됩니다. Base64Url로 인코딩되어 있으며, 헤더에 명시된 알고리즘으로 생성됩니다.

### 클레임이란?
JWT 페이로드에 포함된 정보 단위입니다. 등록된 클레임(iss, exp, sub 등), 공개 클레임, 비공개 클레임으로 구분됩니다. 사용자 정보, 권한, 만료 시간 등을 표현합니다.

