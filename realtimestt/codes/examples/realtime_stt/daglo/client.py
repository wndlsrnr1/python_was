"""
Daglo 실시간 STT gRPC 클라이언트

비동기 gRPC를 통한 실시간 음성 인식 클라이언트입니다.
환경변수 없이 동적으로 API 키와 언어 설정을 받습니다.
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Literal

import grpc.aio

from realtime_stt.daglo import speech_pb2
from realtime_stt.daglo import speech_pb2_grpc

logger = logging.getLogger(__name__)

# 지원하는 언어 코드
SUPPORTED_LANGUAGE_CODES: list[str] = ["ko-KR", "en-US", "mixed"]

# 기본 서버 주소
DEFAULT_SERVER_ADDRESS: str = "apis.daglo.ai:443"


class DagloRealtimeSTTClient:
    """
    Daglo 실시간 STT gRPC 클라이언트

    양방향 스트리밍을 통해 실시간 음성 인식을 수행합니다.
    """

    def __init__(self) -> None:
        """
        클라이언트 초기화
        """
        self.channel: grpc.aio.Channel | None = None
        self.stub: speech_pb2_grpc.SpeechStub | None = None

    async def connect(
        self,
        server_address: str = DEFAULT_SERVER_ADDRESS,
        api_token: str | None = None,
    ) -> None:
        """
        gRPC 서버에 연결합니다.

        Args:
            server_address: gRPC 서버 주소 (기본값: "apis.daglo.ai:443")
            api_token: API 인증 토큰 (필수)

        Raises:
            ValueError: api_token이 None이거나 빈 문자열인 경우
        """
        if not api_token:
            raise ValueError("api_token은 필수입니다")

        logger.info(
            f"[DagloRealtimeSTT] gRPC 연결 시작: " f"server_address={server_address}"
        )

        try:
            # SSL/TLS 보안 채널 생성
            credentials = grpc.ssl_channel_credentials()
            self.channel = grpc.aio.secure_channel(
                server_address,
                credentials,
            )

            # gRPC 스텁 생성
            self.stub = speech_pb2_grpc.SpeechStub(self.channel)

            logger.info(
                f"[DagloRealtimeSTT] gRPC 연결 성공: server_address={server_address}"
            )

        except Exception as e:
            logger.error(
                f"gRPC 연결 실패: server_address={server_address}, " f"error={str(e)}",
                exc_info=True,
            )
            raise

    async def stream_recognize(
        self,
        audio_chunks: AsyncIterator[bytes],
        api_token: str,
        language_code: str = "ko-KR",
        interim_results: bool = True,
        timeout: int = 10800,
    ) -> AsyncIterator[dict[str, str | bool | float]]:
        """
        실시간 STT 스트리밍을 수행합니다.

        Args:
            audio_chunks: 오디오 청크를 비동기적으로 생성하는 제너레이터
            api_token: API 인증 토큰 (필수)
            language_code: 언어 코드 ("ko-KR", "en-US", "mixed")
            interim_results: 임시 결과 반환 여부
            timeout: gRPC 스트림 타임아웃 (초). 기본값: 10800초 (3시간)

        Yields:
            STT 결과 딕셔너리:
            - transcript: 인식된 텍스트
            - is_final: 최종 결과 여부 (True: 최종, False: 임시)
            - language_code: 감지된 언어 코드
            - total_duration: 전체 오디오 지속 시간 (초)

        Raises:
            RuntimeError: 연결되지 않은 경우
            ValueError: 지원하지 않는 언어 코드인 경우
        """
        logger.debug(
            f"[DagloRealtimeSTT] stream_recognize 호출 시작: "
            f"channel={self.channel is not None}, "
            f"stub={self.stub is not None}, "
            f"audio_chunks={audio_chunks is not None}"
        )

        if self.stub is None or self.channel is None:
            logger.error(
                f"[DagloRealtimeSTT] gRPC 연결이 설정되지 않음: "
                f"channel={self.channel is not None}, "
                f"stub={self.stub is not None}"
            )
            raise RuntimeError(
                "gRPC 연결이 설정되지 않았습니다. connect()를 먼저 호출하세요"
            )

        if language_code not in SUPPORTED_LANGUAGE_CODES:
            raise ValueError(
                f"지원하지 않는 언어 코드: {language_code}. "
                f"지원 언어: {', '.join(SUPPORTED_LANGUAGE_CODES)}"
            )

        if not api_token:
            raise ValueError("api_token은 필수입니다")

        # API 인증 메타데이터
        metadata = (("authorization", f"Bearer {api_token}"),)

        logger.info(
            f"[DagloRealtimeSTT] STT 스트리밍 시작: "
            f"language_code={language_code}, "
            f"interim_results={interim_results}, "
            f"timeout={timeout}s"
        )

        try:
            # 요청 제너레이터 생성
            request_iterator = self.Private.create_request_messages(
                audio_chunks,
                language_code,
                interim_results,
            )

            # 양방향 스트리밍 호출
            response_stream = self.stub.StreamingRecognize(
                request_iterator,
                metadata=metadata,
                timeout=timeout,
            )

            # 응답 스트림 처리
            response_count = 0
            async for response in response_stream:
                if response.result:
                    result_dict: dict[str, str | bool | float] = {
                        "transcript": response.result.transcript,
                        "is_final": response.result.is_final,
                        "language_code": response.result.language_code,
                        "total_duration": response.total_duration,
                    }
                    response_count += 1

                    # 응답 수신 로깅
                    result_type = "최종" if response.result.is_final else "임시"

                    logger.info(
                        f"[DagloRealtimeSTT] STT 결과 수신 ({result_type}): "
                        f'transcript="{response.result.transcript}", '
                        f"count={response_count}"
                    )

                    # STT 결과 강조 로깅 (DEBUG)
                    separator = "=" * 50
                    logger.debug(f"[STT-RESULT-GRPC] {separator}")
                    logger.debug("[STT-RESULT-GRPC] === STT 결과 (gRPC 응답) ===")
                    logger.debug(f"[STT-RESULT-GRPC] 타입: [{result_type}]")
                    logger.debug(
                        f'[STT-RESULT-GRPC] Transcript: "{response.result.transcript}"'
                    )
                    logger.debug(
                        f"[STT-RESULT-GRPC] Language: {response.result.language_code}"
                    )
                    logger.debug(
                        f"[STT-RESULT-GRPC] Duration: {response.total_duration:.2f}s"
                    )
                    logger.debug(f"[STT-RESULT-GRPC] Count: {response_count}")
                    logger.debug(f"[STT-RESULT-GRPC] {separator}")

                    yield result_dict

            logger.info(
                f"[DagloRealtimeSTT] STT 스트리밍 종료: " f"총 응답 수={response_count}"
            )

        except grpc.RpcError as e:
            logger.error(
                f"[DagloRealtimeSTT] gRPC 오류 발생: "
                f"code={e.code()}, details={e.details()}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                f"[DagloRealtimeSTT] STT 스트리밍 중 오류 발생: {str(e)}",
                exc_info=True,
            )
            raise

    class Private:
        """내부 헬퍼 메서드"""

        @staticmethod
        async def create_request_messages(
            audio_chunks: AsyncIterator[bytes],
            language_code: str,
            interim_results: bool,
        ) -> AsyncIterator[speech_pb2.StreamingRecognizeRequest]:
            """gRPC 요청 메시지를 생성하는 제너레이터입니다.

            첫 번째 요청은 설정(config)을 포함하고,
            이후 요청은 오디오 데이터(audio_content)를 포함합니다.

            Args:
                audio_chunks: 오디오 청크 비동기 제너레이터
                language_code: 언어 코드
                interim_results: 임시 결과 반환 여부

            Yields:
                StreamingRecognizeRequest 메시지
            """
            # 첫 번째 요청: 설정 전송
            config = speech_pb2.RecognitionConfig(
                language_code=language_code,
                interim_results=interim_results,
            )
            first_request = speech_pb2.StreamingRecognizeRequest(config=config)

            logger.debug(
                f"[DagloRealtimeSTT] 설정 요청 전송: "
                f"language_code={config.language_code}, "
                f"interim_results={config.interim_results}"
            )
            yield first_request

            # 이후 요청: 오디오 데이터 전송
            chunk_count = 0
            total_bytes = 0
            async for audio_chunk in audio_chunks:
                if audio_chunk and len(audio_chunk) > 0:
                    request = speech_pb2.StreamingRecognizeRequest(
                        audio_content=audio_chunk
                    )
                    chunk_count += 1
                    chunk_size = len(audio_chunk)
                    total_bytes += chunk_size

                    logger.debug(
                        f"[DagloRealtimeSTT] 오디오 청크 전송: "
                        f"chunk={chunk_count}, size={chunk_size} bytes"
                    )
                    yield request

            logger.debug(
                f"[DagloRealtimeSTT] 모든 오디오 청크 전송 완료: "
                f"총 청크 수={chunk_count}, 총 크기={total_bytes} bytes"
            )

    async def close(self) -> None:
        """
        gRPC 연결을 종료하고 리소스를 정리합니다.
        """
        if self.channel:
            logger.info(f"[DagloRealtimeSTT] gRPC 연결 종료 시작")
            try:
                await self.channel.close()
                logger.info(f"[DagloRealtimeSTT] gRPC 연결 종료 완료")
            except Exception as e:
                logger.error(
                    f"[DagloRealtimeSTT] gRPC 연결 종료 중 오류 발생: error={str(e)}",
                    exc_info=True,
                )
            finally:
                self.channel = None
                self.stub = None

    async def __aenter__(self) -> DagloRealtimeSTTClient:
        """비동기 컨텍스트 매니저 진입"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """비동기 컨텍스트 매니저 종료"""
        await self.close()
