"""
오디오 형식 변환 어댑터

다양한 오디오 형식(mp4, wav, webm, mp3)을 LINEAR16 PCM 형식으로 변환합니다.
- 샘플레이트: 16000Hz
- 채널: 모노 (1 채널)
- 비트 깊이: 16비트
"""

from __future__ import annotations

import asyncio
import io
import logging
from collections.abc import AsyncIterator
from typing import Literal

from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError

logger = logging.getLogger(__name__)

# 지원하는 입력 형식
SUPPORTED_FORMATS: list[str] = ["mp4", "wav", "webm", "mp3"]

# 목표 오디오 설정
TARGET_SAMPLE_RATE: int = 16000  # 16kHz
TARGET_CHANNELS: int = 1  # 모노
TARGET_SAMPLE_WIDTH: int = 2  # 16비트 (2 bytes)


async def convert_to_linear16(
    audio_bytes: bytes,
    input_format: str,
) -> bytes:
    """
    오디오를 LINEAR16 PCM 형식으로 변환합니다.

    Args:
        audio_bytes: 입력 오디오 바이너리 데이터
        input_format: 입력 오디오 형식 ("mp4", "wav", "webm", "mp3")

    Returns:
        LINEAR16 PCM 형식의 오디오 바이너리 데이터 (16000Hz, 모노, 16비트)

    Raises:
        ValueError: 지원하지 않는 형식이거나 변환 실패 시
    """
    if input_format.lower() not in SUPPORTED_FORMATS:
        raise ValueError(
            f"지원하지 않는 오디오 형식: {input_format}. "
            f"지원 형식: {', '.join(SUPPORTED_FORMATS)}"
        )

    if not audio_bytes or len(audio_bytes) == 0:
        raise ValueError("오디오 데이터가 비어있습니다")

    input_size = len(audio_bytes)
    logger.info(
        f"[AudioAdapter] 오디오 변환 시작: "
        f"format={input_format}, size={input_size} bytes"
    )

    try:
        # BytesIO로 변환하여 pydub에서 사용
        audio_io = io.BytesIO(audio_bytes)

        # pydub로 오디오 로드
        # format 파라미터로 명시적으로 형식 지정
        audio_segment = AudioSegment.from_file(
            audio_io,
            format=input_format.lower(),
        )

        original_frame_rate = audio_segment.frame_rate
        original_channels = audio_segment.channels
        original_sample_width = audio_segment.sample_width
        duration_ms = len(audio_segment)

        logger.debug(
            f"[AudioAdapter] 오디오 로드 완료: "
            f"frame_rate={original_frame_rate}Hz, "
            f"channels={original_channels}, "
            f"sample_width={original_sample_width} bytes, "
            f"duration={duration_ms}ms ({duration_ms / 1000:.2f}s)"
        )

        # 샘플레이트 변환 (16000Hz)
        if audio_segment.frame_rate != TARGET_SAMPLE_RATE:
            old_rate = audio_segment.frame_rate
            audio_segment = audio_segment.set_frame_rate(TARGET_SAMPLE_RATE)
            logger.debug(
                f"[AudioAdapter] 샘플레이트 변환: "
                f"{old_rate}Hz → {TARGET_SAMPLE_RATE}Hz"
            )

        # 채널 변환 (모노)
        if audio_segment.channels != TARGET_CHANNELS:
            old_channels = audio_segment.channels
            audio_segment = audio_segment.set_channels(TARGET_CHANNELS)
            logger.debug(
                f"[AudioAdapter] 채널 변환: "
                f"{old_channels}채널 → {TARGET_CHANNELS}채널"
            )

        # 샘플 너비 변환 (16비트)
        if audio_segment.sample_width != TARGET_SAMPLE_WIDTH:
            old_width = audio_segment.sample_width
            audio_segment = audio_segment.set_sample_width(TARGET_SAMPLE_WIDTH)
            logger.debug(
                f"[AudioAdapter] 샘플 너비 변환: "
                f"{old_width}바이트 → {TARGET_SAMPLE_WIDTH}바이트"
            )

        # LINEAR16 PCM으로 내보내기
        output_io = io.BytesIO()
        audio_segment.export(
            output_io,
            format="raw",
            codec="pcm_s16le",  # LINEAR16 PCM (Little Endian)
        )

        output_bytes = output_io.getvalue()
        output_size = len(output_bytes)
        compression_ratio = (
            (1 - output_size / input_size) * 100 if input_size > 0 else 0
        )
        final_frame_rate = audio_segment.frame_rate
        final_channels = audio_segment.channels
        final_sample_width = audio_segment.sample_width
        final_duration_ms = len(audio_segment)

        logger.info(
            f"[AudioAdapter] 오디오 변환 완료: "
            f"{input_size} bytes → {output_size} bytes"
        )

        return output_bytes

    except CouldntDecodeError as e:
        logger.error(
            f"[AudioAdapter] 오디오 디코딩 실패: "
            f"input_format={input_format}, input_size={input_size} bytes, "
            f"error={str(e)}",
            exc_info=True,
        )
        raise ValueError(f"오디오 디코딩 실패: {str(e)}") from e
    except Exception as e:
        logger.error(
            f"[AudioAdapter] 오디오 변환 중 오류 발생: "
            f"input_format={input_format}, input_size={input_size} bytes, "
            f"error={str(e)}",
            exc_info=True,
        )
        raise ValueError(f"오디오 변환 실패: {str(e)}") from e


def get_supported_formats() -> list[str]:
    """
    지원하는 오디오 형식 목록을 반환합니다.

    Returns:
        지원하는 오디오 형식 리스트
    """
    return SUPPORTED_FORMATS.copy()


class StreamingAudioConverter:
    """
    ffmpeg를 사용한 스트리밍 오디오 변환기

    stdin/stdout 파이프를 통해 WebM 스트림을 LINEAR16 PCM으로 실시간 변환합니다.
    """

    def __init__(self, input_format: str = "webm"):
        """
        Args:
            input_format: 입력 오디오 형식 ("webm", "mp4", "wav", "mp3")
        """
        self.input_format = input_format
        self.process: asyncio.subprocess.Process | None = None
        self._closed = False

    async def __aenter__(self) -> "StreamingAudioConverter":
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
            f"[StreamingAudioConverter] 프로세스 종료 시작: " f"pid={self.process.pid}"
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


async def convert_stream_to_linear16(
    audio_chunks: AsyncIterator[bytes],
    input_format: str = "webm",
) -> AsyncIterator[bytes]:
    """
    오디오 스트림을 LINEAR16 PCM 형식으로 변환합니다.

    Args:
        audio_chunks: WebM 오디오 청크를 비동기적으로 생성하는 제너레이터
        input_format: 입력 오디오 형식 ("webm", "mp4", "wav", "mp3")

    Yields:
        LINEAR16 PCM 형식의 오디오 청크 바이너리 데이터 (16000Hz, 모노, 16비트)
    """
    if input_format.lower() not in SUPPORTED_FORMATS:
        raise ValueError(
            f"지원하지 않는 오디오 형식: {input_format}. "
            f"지원 형식: {', '.join(SUPPORTED_FORMATS)}"
        )

    logger.info(
        f"[StreamingAudioConverter] 스트림 변환 시작: " f"input_format={input_format}"
    )

    converter = StreamingAudioConverter(input_format=input_format)
    chunk_count = 0
    pcm_chunk_count = 0

    try:
        async with converter:
            # 백그라운드 태스크: WebM 청크를 stdin에 전송
            async def write_chunks() -> None:
                nonlocal chunk_count
                try:
                    async for chunk in audio_chunks:
                        if chunk and len(chunk) > 0:
                            chunk_count += 1
                            await converter.write_chunk(chunk)
                            logger.debug(
                                f"[StreamingAudioConverter] WebM 청크 전송: "
                                f"chunk={chunk_count}, size={len(chunk)} bytes"
                            )
                except Exception as e:
                    logger.error(
                        f"[StreamingAudioConverter] WebM 청크 전송 중 오류: {str(e)}",
                        exc_info=True,
                    )
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
                        f"[StreamingAudioConverter] PCM 청크 생성: "
                        f"chunk={pcm_chunk_count}, size={len(pcm_chunk)} bytes"
                    )
                    yield pcm_chunk

            except Exception as e:
                logger.error(
                    f"[StreamingAudioConverter] PCM 청크 읽기 중 오류: {str(e)}",
                    exc_info=True,
                )
                raise
            finally:
                # write_task 완료 대기
                try:
                    await write_task
                except Exception as e:
                    logger.warning(
                        f"[StreamingAudioConverter] write_task 완료 대기 중 오류: {str(e)}"
                    )

        logger.info(
            f"[StreamingAudioConverter] 스트림 변환 완료: "
            f"input_chunks={chunk_count}, output_chunks={pcm_chunk_count}"
        )

    except Exception as e:
        logger.error(
            f"[StreamingAudioConverter] 스트림 변환 중 오류: {str(e)}",
            exc_info=True,
        )
        raise ValueError(f"스트림 변환 실패: {str(e)}") from e
