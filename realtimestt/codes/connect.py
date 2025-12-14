async def connect(self):
    scope = self.scope
    client_host = scope.get("client", [None, None])[0] if scope.get("client") else "unknown"

    try:
        await self.accept()

        # 세션 상태 초기화
        self.session_id = None
        self.session = None
        self.user = None
        self.base_path = None
        self.metadata = {}
        self.sequence_number = 0
        self.chunk_count = 0
        self.start_time = timezone.now()

        # STT 처리 관련 상태
        self.audio_queue = None
        self.stt_processing_task = None
        self.input_format = "webm"
        self.language_code = "ko-KR"
        self.interim_results = True

        # 사용자 정보 확인
        user = scope.get("user")
        if user and user.is_authenticated:
            logger.info(f"WebSocket 연결 수립 성공: user_id={user.id}")
        else:
            logger.warning("WebSocket 연결 수립 (인증 없음)")

    except Exception as e:
        logger.error(f"WebSocket 연결 수립 실패: {str(e)}")
        raise