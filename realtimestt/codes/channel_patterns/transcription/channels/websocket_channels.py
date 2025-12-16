"""
WebSocket Channel 구현

Django Channels의 AsyncWebsocketConsumer를 Channel 패턴으로 추상화한 WebSocketChannel.
WebSocket 메시지 수신을 큐 기반으로 처리하고, 메시지 전송을 지원합니다.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from channels.generic.websocket import AsyncWebsocketConsumer


class WebSocketChannel:
    """
    WebSocket을 Channel 패턴으로 추상화한 WebSocketChannel

    Channel 패턴을 따르며, WebSocket 메시지 수신을 큐 기반으로 처리하고,
    메시지 전송을 지원합니다.
    """

    def __init__(
        self, websocket: "AsyncWebsocketConsumer", timeout: float = 1.0
    ) -> None:
        """
        Args:
            websocket: Django Channels AsyncWebsocketConsumer 인스턴스
            timeout: 큐에서 데이터를 가져올 때의 타임아웃 (초, 기본값: 1.0)
        """
        self._websocket = websocket
        self._timeout = timeout
        self._queue: asyncio.Queue[bytes | str | None] = asyncio.Queue()
        self._closed = False

    async def send(
        self,
        text_data: str | None = None,
        bytes_data: bytes | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """
        WebSocket으로 메시지 전송

        Args:
            text_data: 텍스트 메시지 (JSON 문자열 등)
            bytes_data: 바이너리 메시지
            data: 딕셔너리 데이터 (JSON으로 변환하여 text_data로 전송)

        Raises:
            RuntimeError: Channel이 이미 종료되었거나 WebSocket 연결이 끊어진 경우
            ValueError: 파라미터가 모두 None이거나 여러 파라미터가 동시에 제공된 경우
        """
        if self._closed:
            raise RuntimeError("Channel이 이미 종료되었습니다")

        # 파라미터 검증
        provided_params = sum(
            [
                text_data is not None,
                bytes_data is not None,
                data is not None,
            ]
        )

        if provided_params == 0:
            logger.warning("[WebSocketChannel] 전송할 데이터가 없습니다")
            return

        if provided_params > 1:
            raise ValueError("text_data, bytes_data, data 중 하나만 제공해야 합니다")

        try:
            # dict 타입은 JSON으로 변환
            if data is not None:
                text_data = json.dumps(data, ensure_ascii=False)
                bytes_data = None

            # WebSocket으로 전송
            if text_data is not None:
                await self._websocket.send(text_data=text_data)
                logger.debug(
                    f"[WebSocketChannel] 텍스트 메시지 전송: "
                    f"length={len(text_data)} bytes"
                )
            elif bytes_data is not None:
                await self._websocket.send(bytes_data=bytes_data)
                logger.debug(
                    f"[WebSocketChannel] 바이너리 메시지 전송: "
                    f"length={len(bytes_data)} bytes"
                )

        except Exception as e:
            logger.error(
                f"[WebSocketChannel] WebSocket 전송 실패: {str(e)}",
                exc_info=True,
            )
            raise

    async def receive_message(
        self,
        text_data: str | None = None,
        bytes_data: bytes | None = None,
    ) -> None:
        """
        Consumer의 receive()에서 호출하여 메시지를 큐에 추가

        Args:
            text_data: 수신한 텍스트 메시지
            bytes_data: 수신한 바이너리 메시지
        """
        if self._closed:
            logger.warning("[WebSocketChannel] 종료된 Channel에 메시지 수신 시도")
            return

        if text_data is not None:
            await self._queue.put(text_data)
            logger.debug(
                f"[WebSocketChannel] 텍스트 메시지 수신: "
                f"length={len(text_data)} bytes"
            )
        elif bytes_data is not None:
            await self._queue.put(bytes_data)
            logger.debug(
                f"[WebSocketChannel] 바이너리 메시지 수신: "
                f"length={len(bytes_data)} bytes"
            )
        else:
            logger.warning("[WebSocketChannel] 빈 메시지 수신, 무시합니다")

    async def close(self) -> None:
        """Channel 종료 신호 전송"""
        if self._closed:
            return

        self._closed = True
        await self._queue.put(None)
        logger.debug("[WebSocketChannel] 종료 신호 전송")

    async def receive(self) -> AsyncIterator[bytes | str]:
        """
        async for에서 사용 가능한 receive 메서드

        send()에 대응하는 메서드로, WebSocket 메시지를 받습니다.

        Yields:
            bytes | str: WebSocket 메시지 (텍스트 또는 바이너리)
        """
        async for item in self:
            yield item

    def __aiter__(self) -> AsyncIterator[bytes | str]:
        """async for를 사용할 수 있도록 iterator 인터페이스 제공"""
        return self._generate()

    async def _generate(self) -> AsyncIterator[bytes | str]:
        """
        내부 generator

        큐에서 WebSocket 메시지를 가져와 yield합니다.
        """
        message_count = 0

        try:
            while True:
                try:
                    message = await asyncio.wait_for(
                        self._queue.get(), timeout=self._timeout
                    )

                    if message is None:
                        logger.info(
                            f"[WebSocketChannel] 종료 신호 수신, "
                            f"총 {message_count}개 메시지 처리"
                        )
                        break

                    message_count += 1
                    message_type = "텍스트" if isinstance(message, str) else "바이너리"
                    logger.debug(
                        f"[WebSocketChannel] 메시지 처리: "
                        f"message={message_count}, "
                        f"type={message_type}, "
                        f"length={len(message)} bytes"
                    )
                    yield message

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(
                        f"[WebSocketChannel] 메시지 처리 중 오류: {str(e)}",
                        exc_info=True,
                    )
                    break

        except Exception as e:
            logger.error(
                f"[WebSocketChannel] 제너레이터 실행 중 오류: {str(e)}",
                exc_info=True,
            )
            raise
