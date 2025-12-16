"""
gRPC Channel 구현

DagloRealtimeSTTClient와 audio queue를 내부화한 gRPC Channel.
Channel 패턴을 따르며, PCM 오디오 청크를 입력받아 STT 결과를 출력합니다.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

logger = logging.getLogger(__name__)

# DagloRealtimeSTTClient import 시도
try:
    from realtime_stt.daglo.client import DagloRealtimeSTTClient
except ImportError:
    # 상대 경로로 시도
    try:
        import sys
        from pathlib import Path

        # examples 폴더를 sys.path에 추가
        examples_path = Path(__file__).parent.parent.parent.parent / "examples"
        if examples_path.exists() and str(examples_path) not in sys.path:
            sys.path.insert(0, str(examples_path))

        from realtime_stt.daglo.client import DagloRealtimeSTTClient
    except ImportError:
        logger.error(
            "DagloRealtimeSTTClient를 import할 수 없습니다. "
            "realtime_stt.daglo.client 경로를 확인하세요."
        )
        raise

# 지원하는 언어 코드
SUPPORTED_LANGUAGE_CODES: list[str] = ["ko-KR", "en-US", "mixed"]

# 기본 서버 주소
DEFAULT_SERVER_ADDRESS: str = "apis.daglo.ai:443"


class gRPCChannel:
    """
    DagloRealtimeSTTClient와 audio queue를 내부화한 gRPC Channel

    Channel 패턴을 따르며, PCM 오디오 청크를 입력받아 STT 결과를 출력합니다.
    """

    def __init__(
        self,
        api_token: str,
        server_address: str = DEFAULT_SERVER_ADDRESS,
        language_code: str = "ko-KR",
        interim_results: bool = True,
        timeout: int = 10800,
    ) -> None:
        """
        Args:
            api_token: API 인증 토큰 (필수)
            server_address: gRPC 서버 주소 (기본값: "apis.daglo.ai:443")
            language_code: 언어 코드 ("ko-KR", "en-US", "mixed")
            interim_results: 임시 결과 반환 여부 (기본값: True)
            timeout: gRPC 스트림 타임아웃 (초, 기본값: 10800)
        """
        if not api_token:
            raise ValueError("api_token은 필수입니다")

        if language_code not in SUPPORTED_LANGUAGE_CODES:
            raise ValueError(
                f"지원하지 않는 언어 코드: {language_code}. "
                f"지원 언어: {', '.join(SUPPORTED_LANGUAGE_CODES)}"
            )

        self._api_token = api_token
        self._server_address = server_address
        self._language_code = language_code
        self._interim_results = interim_results
        self._timeout = timeout

        self._queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self._client: DagloRealtimeSTTClient | None = None
        self._closed = False

    async def send(self, chunk: bytes) -> None:
        """
        PCM 오디오 청크를 내부 큐에 추가합니다.

        Args:
            chunk: PCM 오디오 청크 바이너리 데이터
        """
        if self._closed:
            raise RuntimeError("Channel이 이미 종료되었습니다")

        if not chunk or len(chunk) == 0:
            return

        await self._queue.put(chunk)

    async def close(self) -> None:
        """Channel 종료 신호 전송 및 gRPC 연결 정리"""
        if self._closed:
            return

        self._closed = True
        await self._queue.put(None)

        # gRPC 클라이언트 연결 종료
        if self._client:
            try:
                await self._client.close()
                logger.debug("[gRPCChannel] gRPC 클라이언트 연결 종료 완료")
            except Exception as e:
                logger.warning(
                    f"[gRPCChannel] gRPC 클라이언트 연결 종료 중 오류: {str(e)}"
                )

    async def receive(self) -> AsyncIterator[dict[str, str | bool | float]]:
        """
        async for에서 사용 가능한 receive 메서드

        send()에 대응하는 메서드로, STT 결과를 받습니다.

        Yields:
            dict[str, str | bool | float]: STT 결과 딕셔너리
                - transcript: str - 인식된 텍스트
                - is_final: bool - 최종 결과 여부
                - language_code: str - 언어 코드
                - total_duration: float - 전체 오디오 지속 시간 (초)
        """
        async for item in self:
            yield item

    def __aiter__(self) -> AsyncIterator[dict[str, str | bool | float]]:
        """async for를 사용할 수 있도록 iterator 인터페이스 제공"""
        return self._generate()

    async def _generate(self) -> AsyncIterator[dict[str, str | bool | float]]:
        """
        내부 generator

        큐에서 PCM 청크를 가져와 gRPC로 전송한 후 STT 결과를 yield합니다.
        """
        client = DagloRealtimeSTTClient()
        self._client = client
        chunk_count = 0
        result_count = 0

        try:
            # gRPC 연결
            await client.connect(
                server_address=self._server_address,
                api_token=self._api_token,
            )

            logger.info(
                f"[gRPCChannel] gRPC 연결 완료: "
                f"server_address={self._server_address}, "
                f"language_code={self._language_code}"
            )

            # 백그라운드 태스크: 큐에서 PCM 청크를 읽어 AsyncIterator로 변환
            async def read_chunks() -> AsyncIterator[bytes]:
                """큐에서 PCM 청크를 읽어 yield하는 async generator"""
                nonlocal chunk_count
                try:
                    while True:
                        try:
                            chunk = await asyncio.wait_for(
                                self._queue.get(), timeout=1.0
                            )

                            if chunk is None:
                                break

                            chunk_count += 1
                            logger.debug(
                                f"[gRPCChannel] PCM 청크 전송: "
                                f"chunk={chunk_count}, size={len(chunk)} bytes"
                            )
                            yield chunk
                        except asyncio.TimeoutError:
                            continue
                        except Exception as e:
                            logger.error(
                                f"[gRPCChannel] PCM 청크 읽기 중 오류: {str(e)}",
                                exc_info=True,
                            )
                            break
                except Exception as e:
                    logger.error(
                        f"[gRPCChannel] 청크 읽기 태스크 중 오류: {str(e)}",
                        exc_info=True,
                    )

            # gRPC 스트리밍 시작
            async for stt_result in client.stream_recognize(
                read_chunks(),
                api_token=self._api_token,
                language_code=self._language_code,
                interim_results=self._interim_results,
                timeout=self._timeout,
            ):
                result_count += 1
                logger.debug(
                    f"[gRPCChannel] STT 결과 수신: "
                    f"result={result_count}, "
                    f"transcript={stt_result.get('transcript', '')[:50]}..."
                )
                yield stt_result

            logger.info(
                f"[gRPCChannel] STT 스트리밍 완료: "
                f"input_chunks={chunk_count}, output_results={result_count}"
            )

        except Exception as e:
            logger.error(
                f"[gRPCChannel] STT 스트리밍 중 오류: {str(e)}",
                exc_info=True,
            )
            raise
        finally:
            # gRPC 연결 종료
            if client:
                try:
                    await client.close()
                except Exception as e:
                    logger.warning(
                        f"[gRPCChannel] gRPC 클라이언트 종료 중 오류: {str(e)}"
                    )
            self._client = None
