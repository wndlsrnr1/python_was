"""
Stream Pipeline 실행 예제

StrChannel을 사용하여 Pipeline을 실행하는 예제입니다.
"""

import asyncio
import logging

from channel.pipeline import StreamPipeline

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def main() -> None:
    """Pipeline 실행 예제"""
    pipeline = StreamPipeline(timeout=1.0)

    # Producer: 문자열을 StrChannel에 전송
    async def producer() -> None:
        """문자열을 Pipeline에 전송"""
        strings = ["1", "2", "3", "4", "5"]

        for text in strings:
            await pipeline.str_channel.send(text)
            logger.info(f"[Producer] 전송: {text}")
            await asyncio.sleep(0.1)  # 시뮬레이션

        # 종료 신호
        await pipeline.str_channel.close()
        logger.info("[Producer] 전송 완료")

    # Consumer: BytesToStrStream에서 최종 결과 수신
    async def consumer() -> None:
        """Pipeline의 최종 결과를 수신"""
        async for result in pipeline.bytes_to_str_stream.receive():
            logger.info(f"[Consumer] 수신: {result}")

    # Pipeline과 Producer, Consumer를 병렬로 실행
    await asyncio.gather(
        pipeline.start(),  # Pipeline 시작
        producer(),  # Producer 실행
        consumer(),  # Consumer 실행
    )

    logger.info("[Main] 모든 작업 완료")


if __name__ == "__main__":
    asyncio.run(main())
