import asyncio
from .bytes_to_str_stream import BytesToStrStream
from .number_to_bytes_stream import NumberToBytesStream
from .str_channel import StrChannel
from .str_to_number_stream import StrToNumberStream


# 파이프라인에서
class StreamPipeline:
    def __init__(self, timeout: float = 1.0) -> None:
        # 각 채널들을 참조함
        self.str_channel = StrChannel(timeout=timeout)
        self.str_to_number_stream = StrToNumberStream(timeout=timeout)
        self.number_to_bytes_stream = NumberToBytesStream(timeout=timeout)
        self.bytes_to_str_stream = BytesToStrStream(timeout=timeout)

        # 이 파이프라인이 작동하는지
        self._running = False
        # task는 왜등록?
        self._task: list[asyncio.Task[None]] = []

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        try:
            self._task = [
                asyncio.create_task(self._str_to_number()),
                asyncio.create_task(self._number_to_bytes()),
                asyncio.create_task(self._bytes_to_str()),
            ]

            await asyncio.gather(*self._task, return_exceptions=True)
        except Exception as e:
            raise
        finally:
            self._running = False

    async def _str_to_number(self) -> None:
        try:
            async for text in self.str_channel.receive():
                await self.str_to_number_stream.send(text)
        except Exception as e:
            raise
        finally:
            await self.str_to_number_stream.close()

    async def _number_to_bytes(self) -> None:
        try:
            async for number in self.str_to_number_stream.receive():
                await self.number_to_bytes_stream.send(number)
        except Exception as e:
            raise
        finally:
            await self.number_to_bytes_stream.close()

    async def _bytes_to_str(self) -> None:
        try:
            async for bytes_data in self.number_to_bytes_stream.receive():
                await self.bytes_to_str_stream.send(bytes_data)
        except Exception as e:
            raise
        finally:
            await self.bytes_to_str_stream.close()

    async def close_all(self) -> None:
        """
        모든 Stream 종료

        Pipeline의 모든 Stream을 안전하게 종료합니다.
        """

        # 실행 중인 태스크 취소
        if self._task:
            for task in self._task:
                if not task.done():
                    task.cancel()

            # 태스크 완료 대기
            try:
                await asyncio.gather(*self._task, return_exceptions=True)
            except Exception as e:
                raise

        # 모든 Stream 종료
        try:
            await self.str_channel.close()
        except Exception as e:
            raise

        try:
            await self.str_to_number_stream.close()
        except Exception as e:
            raise

        try:
            await self.number_to_bytes_stream.close()
        except Exception as e:
            raise

        try:
            await self.bytes_to_str_stream.close()
        except Exception as e:
            raise

        self._running = False
