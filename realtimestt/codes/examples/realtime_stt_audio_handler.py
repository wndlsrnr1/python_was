"""
실시간 STT 오디오 청크 처리 Handler
"""

import asyncio
import logging
from collections.abc import AsyncIterator

logger = logging.getLogger(__name__)


class AudioHandler:
    """오디오 청크 처리 Handler"""

    async def generate_chunks(
        self, audio_queue: asyncio.Queue[bytes]
    ) -> AsyncIterator[bytes]:
        """오디오 청크를 비동기적으로 생성하는 제너레이터

        큐에서 오디오 청크를 가져와 yield합니다.
        None이 들어오면 종료합니다.

        Args:
            audio_queue: 오디오 청크를 담는 큐

        Yields:
            오디오 청크 바이너리 데이터
        """
        chunk_count = 0

        while True:
            try:
                chunk = await asyncio.wait_for(
                    audio_queue.get(),
                    timeout=1.0,
                )

                if chunk is None:
                    break

                chunk_count += 1
                yield chunk

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(
                    f"오디오 청크 생성 중 오류: chunk_count={chunk_count}, error={str(e)}",
                    exc_info=True,
                )
                break
