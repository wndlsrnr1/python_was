가능합니다. 각 단계별 Channel을 분리하고, 상위에서 통합 관리하는 패턴이 적합합니다.


[1 tool called]


가능합니다. 각 단계별 Channel을 두고, 상위에서 통합 관리하는 패턴입니다.

## Pipeline 패턴 (Composite Channel)

```python
import asyncio
from typing import AsyncIterator


class Channel:
    """기본 Channel 클래스"""
    
    def __init__(self, timeout: float = 1.0) -> None:
        self._queue: asyncio.Queue[str | None] = asyncio.Queue()
        self._timeout = timeout

    async def send(self, item: str) -> None:
        await self._queue.put(item)

    async def close(self) -> None:
        await self._queue.put(None)

    def __aiter__(self) -> AsyncIterator[str]:
        return self._generate()

    async def _generate(self) -> AsyncIterator[str]:
        count = 0
        while True:
            try:
                item = await asyncio.wait_for(self._queue.get(), timeout=self._timeout)
                if item is None:
                    print(f"[Channel] 종료 신호 수신, 총 {count}개 처리")
                    break
                count += 1
                yield item
            except asyncio.TimeoutError:
                continue
            except Exception:
                break


class StreamPipeline:
    """여러 Channel을 통합 관리하는 Pipeline"""
    
    def __init__(self) -> None:
        # 각 단계별 Channel
        self.socket_channel = Channel()
        self.ffmpeg_channel = Channel()
        self.grpc_channel = Channel()
        
        # Pipeline 전체 생명주기 관리
        self._is_running = False
    
    async def start(self) -> None:
        """Pipeline 시작"""
        self._is_running = True
        # 모든 Channel을 병렬로 실행
        await asyncio.gather(
            self._socket_to_ffmpeg(),
            self._ffmpeg_to_grpc(),
            self._consume_grpc(),
        )
    
    async def _socket_to_ffmpeg(self) -> None:
        """Socket → FFmpeg 파이프라인"""
        async for data in self.socket_channel:
            # FFmpeg 변환 로직
            converted = f"[FFmpeg 변환] {data}"
            await self.ffmpeg_channel.send(converted)
        await self.ffmpeg_channel.close()
    
    async def _ffmpeg_to_grpc(self) -> None:
        """FFmpeg → gRPC 파이프라인"""
        async for data in self.ffmpeg_channel:
            # gRPC 전송 준비
            ready = f"[gRPC 준비] {data}"
            await self.grpc_channel.send(ready)
        await self.grpc_channel.close()
    
    async def _consume_grpc(self) -> None:
        """gRPC 소비"""
        async for data in self.grpc_channel:
            print(f"[gRPC 전송] {data}")
    
    async def close_all(self) -> None:
        """모든 Channel 종료"""
        await self.socket_channel.close()


# 사용 예시
async def socket_reader(pipeline: StreamPipeline) -> None:
    """Socket에서 데이터 읽기"""
    items = [f"데이터{i+1}" for i in range(5)]
    for item in items:
        await asyncio.sleep(0.2)
        await pipeline.socket_channel.send(item)
    await pipeline.socket_channel.close()


async def app() -> None:
    pipeline = StreamPipeline()
    
    # Socket Reader와 Pipeline을 병렬 실행
    await asyncio.gather(
        socket_reader(pipeline),
        pipeline.start(),
    )


asyncio.run(app())
```

## 장점

1. 관심사 분리: 각 Channel이 독립적으로 관리됨
2. 재사용성: 각 Channel을 다른 파이프라인에서도 사용 가능
3. 테스트 용이성: 각 단계를 독립적으로 테스트 가능
4. 생명주기 관리: `StreamPipeline`이 전체를 제어

## 더 간단한 버전 (필요시)

```python
class StreamPipeline:
    """단순화된 Pipeline"""
    
    def __init__(self) -> None:
        self.channels = {
            'socket': Channel(),
            'ffmpeg': Channel(),
            'grpc': Channel(),
        }
    
    async def close_all(self) -> None:
        """모든 Channel 한 번에 종료"""
        await asyncio.gather(*[ch.close() for ch in self.channels.values()])
```

이 패턴으로 각 단계의 독립성과 전체 통합 관리의 장점을 모두 얻을 수 있습니다.