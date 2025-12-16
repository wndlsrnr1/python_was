import asyncio
from channels.channel.bytes_to_str_stream import BytesToStrStream
from channels.channel.number_to_bytes_stream import NumberToBytesStream
from channels.channel.str_channel import StrChannel
from channels.channel.str_to_number_stream import StrToNumberStream


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
