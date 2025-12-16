"""
Audio Channel 구현

ffmpeg와 audio queue를 내부화한 Audio Channel.
Channel 패턴을 따르며, WebM 오디오 청크를 입력받아 LINEAR16 PCM으로 변환하여 출력합니다.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator

logger = logging.getLogger(__name__)

# 지원하는 입력 형식
SUPPORTED_FORMATS: list[str] = ["mp4", "wav", "webm", "mp3"]

# 목표 오디오 설정
TARGET_SAMPLE_RATE: int = 16000  # 16kHz
TARGET_CHANNELS: int = 1  # 모노


class StreamingAudioConverter:
    """
    ffmpeg를 사용한 스트리밍 오디오 변환기

    stdin/stdout 파이프를 통해 WebM 스트림을 LINEAR16 PCM으로 실시간 변환합니다.
    """

    def __init__(self, input_format: str = "webm") -> None:
        """
        Args:
            input_format: 입력 오디오 형식 ("webm", "mp4", "wav", "mp3")
        """
        self.input_format = input_format
        self.process: asyncio.subprocess.Process | None = None
        self._closed = False

    async def __aenter__(self) -> StreamingAudioConverter:
        """ffmpeg 프로세스 시작"""
        if self.process is not None:
            raise RuntimeError("프로세스가 이미 시작되었습니다")

        logger.info(
            f"[StreamingAudioConverter] ffmpeg 프로세스 시작: "
            f"input_format={self.input_format}"
        )

        # ffmpeg 명령어 구성
        cmd = [
            "ffmpeg",
            "-i",
            "pipe:0",  # stdin에서 입력
            "-f",
            "s16le",  # 출력 형식 (signed 16-bit little-endian)
            "-ar",
            str(TARGET_SAMPLE_RATE),  # 샘플레이트 16kHz
            "-ac",
            str(TARGET_CHANNELS),  # 모노 채널
            "-acodec",
            "pcm_s16le",  # PCM 코덱
            "-loglevel",
            "error",  # 에러만 로깅
            "pipe:1",  # stdout으로 출력
        ]

        try:
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            logger.debug(
                f"[StreamingAudioConverter] ffmpeg 프로세스 생성 완료: "
                f"pid={self.process.pid if self.process else None}"
            )

            return self

        except Exception as e:
            logger.error(
                f"[StreamingAudioConverter] ffmpeg 프로세스 생성 실패: {str(e)}",
                exc_info=True,
            )
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """프로세스 종료 및 정리"""
        await self.close()

    async def write_chunk(self, chunk: bytes) -> None:
        """
        WebM 청크를 stdin에 전송합니다.

        Args:
            chunk: WebM 오디오 청크 바이너리 데이터
        """
        if self.process is None or self.process.stdin is None:
            raise RuntimeError("프로세스가 시작되지 않았습니다")

        if self._closed:
            raise RuntimeError("프로세스가 이미 종료되었습니다")

        try:
            self.process.stdin.write(chunk)
            await self.process.stdin.drain()
        except Exception as e:
            logger.error(
                f"[StreamingAudioConverter] 청크 전송 실패: {str(e)}",
                exc_info=True,
            )
            raise

    async def read_pcm_chunk(self, chunk_size: int = 8192) -> bytes:
        """
        stdout에서 PCM 청크를 읽습니다.

        Args:
            chunk_size: 읽을 청크 크기 (기본값: 8192 bytes)

        Returns:
            PCM 오디오 청크 바이너리 데이터
        """
        if self.process is None or self.process.stdout is None:
            raise RuntimeError("프로세스가 시작되지 않았습니다")

        if self._closed:
            return b""

        try:
            chunk = await self.process.stdout.read(chunk_size)
            return chunk
        except Exception as e:
            logger.error(
                f"[StreamingAudioConverter] PCM 청크 읽기 실패: {str(e)}",
                exc_info=True,
            )
            raise

    async def flush(self) -> None:
        """남은 데이터 처리 및 stdin 닫기"""
        if self.process is None or self.process.stdin is None:
            return

        if self._closed:
            return

        try:
            self.process.stdin.close()
            await self.process.stdin.wait_closed()
            logger.debug("[StreamingAudioConverter] stdin 닫기 완료")
        except Exception as e:
            logger.error(
                f"[StreamingAudioConverter] stdin 닫기 실패: {str(e)}",
                exc_info=True,
            )

    async def close(self) -> None:
        """프로세스 종료 및 정리"""
        if self._closed:
            return

        self._closed = True

        if self.process is None:
            return

        logger.info(
            f"[StreamingAudioConverter] 프로세스 종료 시작: pid={self.process.pid}"
        )

        try:
            # stdin 닫기
            if self.process.stdin and not self.process.stdin.is_closing():
                try:
                    self.process.stdin.close()
                    await self.process.stdin.wait_closed()
                except Exception as e:
                    logger.warning(
                        f"[StreamingAudioConverter] stdin 닫기 중 오류: {str(e)}"
                    )

            # 프로세스 종료 대기
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
                return_code = self.process.returncode
                logger.debug(
                    f"[StreamingAudioConverter] 프로세스 종료 완료: "
                    f"pid={self.process.pid}, return_code={return_code}"
                )
            except asyncio.TimeoutError:
                logger.warning(
                    f"[StreamingAudioConverter] 프로세스 종료 타임아웃, 강제 종료: "
                    f"pid={self.process.pid}"
                )
                self.process.kill()
                await self.process.wait()
                logger.debug(
                    f"[StreamingAudioConverter] 프로세스 강제 종료 완료: "
                    f"pid={self.process.pid}"
                )

            # stderr 읽기 (에러 로깅)
            if self.process.stderr:
                try:
                    stderr_data = await asyncio.wait_for(
                        self.process.stderr.read(), timeout=1.0
                    )
                    if stderr_data:
                        stderr_text = stderr_data.decode("utf-8", errors="ignore")
                        if stderr_text.strip():
                            logger.warning(
                                f"[StreamingAudioConverter] ffmpeg stderr: {stderr_text}"
                            )
                except asyncio.TimeoutError:
                    pass
                except Exception as e:
                    logger.warning(
                        f"[StreamingAudioConverter] stderr 읽기 중 오류: {str(e)}"
                    )

        except Exception as e:
            logger.error(
                f"[StreamingAudioConverter] 프로세스 종료 중 오류: {str(e)}",
                exc_info=True,
            )
        finally:
            self.process = None


class AudioChannel:
    """
    ffmpeg와 audio queue를 내부화한 Audio Channel

    Channel 패턴을 따르며, WebM 오디오 청크를 입력받아 LINEAR16 PCM으로 변환하여 출력합니다.
    """

    def __init__(self, input_format: str = "webm", timeout: float = 1.0) -> None:
        """
        Args:
            input_format: 입력 오디오 형식 ("webm", "mp4", "wav", "mp3")
            timeout: 큐에서 데이터를 가져올 때의 타임아웃 (초)
        """
        if input_format.lower() not in SUPPORTED_FORMATS:
            raise ValueError(
                f"지원하지 않는 오디오 형식: {input_format}. "
                f"지원 형식: {', '.join(SUPPORTED_FORMATS)}"
            )

        self.input_format = input_format.lower()
        self._timeout = timeout
        self._queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self._closed = False

    async def send(self, chunk: bytes) -> None:
        """
        WebM 오디오 청크를 내부 큐에 추가합니다.

        Args:
            chunk: WebM 오디오 청크 바이너리 데이터
        """
        if self._closed:
            raise RuntimeError("Channel이 이미 종료되었습니다")

        if not chunk or len(chunk) == 0:
            return

        await self._queue.put(chunk)

    async def close(self) -> None:
        """Channel 종료 신호 전송"""
        if self._closed:
            return

        self._closed = True
        await self._queue.put(None)

    async def receive(self) -> AsyncIterator[bytes]:
        """
        async for에서 사용 가능한 receive 메서드

        send()에 대응하는 메서드로, PCM 오디오 청크를 받습니다.

        Yields:
            bytes: PCM 오디오 청크 바이너리 데이터
        """
        async for item in self:
            yield item

    def __aiter__(self) -> AsyncIterator[bytes]:
        """async for를 사용할 수 있도록 iterator 인터페이스 제공"""
        return self._generate()

    async def _generate(self) -> AsyncIterator[bytes]:
        """
        내부 generator

        큐에서 WebM 청크를 가져와 ffmpeg로 변환한 후 PCM 청크를 yield합니다.
        """
        converter = StreamingAudioConverter(input_format=self.input_format)
        chunk_count = 0
        pcm_chunk_count = 0

        try:
            async with converter:
                # 백그라운드 태스크: 큐에서 WebM 청크를 읽어 converter에 전송
                async def write_chunks() -> None:
                    nonlocal chunk_count
                    try:
                        while True:
                            try:
                                chunk = await asyncio.wait_for(
                                    self._queue.get(), timeout=self._timeout
                                )

                                if chunk is None:
                                    break

                                chunk_count += 1
                                await converter.write_chunk(chunk)
                                logger.debug(
                                    f"[AudioChannel] WebM 청크 전송: "
                                    f"chunk={chunk_count}, size={len(chunk)} bytes"
                                )
                            except asyncio.TimeoutError:
                                continue
                            except Exception as e:
                                logger.error(
                                    f"[AudioChannel] WebM 청크 전송 중 오류: {str(e)}",
                                    exc_info=True,
                                )
                                break
                    finally:
                        await converter.flush()

                # 백그라운드 태스크 시작
                write_task = asyncio.create_task(write_chunks())

                # stdout에서 PCM 청크 읽기
                try:
                    while True:
                        pcm_chunk = await converter.read_pcm_chunk()
                        if not pcm_chunk:
                            break

                        pcm_chunk_count += 1
                        logger.debug(
                            f"[AudioChannel] PCM 청크 생성: "
                            f"chunk={pcm_chunk_count}, size={len(pcm_chunk)} bytes"
                        )
                        yield pcm_chunk

                except Exception as e:
                    logger.error(
                        f"[AudioChannel] PCM 청크 읽기 중 오류: {str(e)}",
                        exc_info=True,
                    )
                    raise
                finally:
                    # write_task 완료 대기
                    try:
                        await write_task
                    except Exception as e:
                        logger.warning(
                            f"[AudioChannel] write_task 완료 대기 중 오류: {str(e)}"
                        )

            logger.info(
                f"[AudioChannel] 스트림 변환 완료: "
                f"input_chunks={chunk_count}, output_chunks={pcm_chunk_count}"
            )

        except Exception as e:
            logger.error(
                f"[AudioChannel] 스트림 변환 중 오류: {str(e)}",
                exc_info=True,
            )
            raise
