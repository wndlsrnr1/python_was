# """
# Stream Pipeline 구현

# 여러 Stream을 연결하여 비동기로 데이터를 흘려보내는 Pipeline입니다.
# StrChannel → StrToNumberStream → NumberToBytesStream → BytesToStrStream 순서로 처리합니다.
# """

# import asyncio
# import logging
# from typing import TYPE_CHECKING

# from channel.str_channel import StrChannel
# from channel.str_to_number_stream import StrToNumberStream
# from channel.number_to_bytes_stream import NumberToBytesStream
# from channel.bytes_to_str_stream import BytesToStrStream

# logger = logging.getLogger(__name__)


# class StreamPipelineV2:
#     """
#     Stream 전체 파이프라인

#     여러 Stream을 연결하여 비동기로 데이터를 흘려보냅니다.
#     StrChannel → StrToNumberStream → NumberToBytesStream → BytesToStrStream 순서로 처리합니다.
#     """

#     def __init__(self, timeout: float = 1.0) -> None:
#         """
#         Args:
#             timeout: 큐에서 데이터를 가져올 때의 타임아웃 (초, 기본값: 1.0)
#         """
#         # 각 단계별 Stream 생성
#         self.str_channel = StrChannel(timeout=timeout)
#         self.str_to_number_stream = StrToNumberStream(timeout=timeout)
#         self.number_to_bytes_stream = NumberToBytesStream(timeout=timeout)
#         self.bytes_to_str_stream = BytesToStrStream(timeout=timeout)

#         self._running = False
#         self._tasks: list[asyncio.Task[None]] = []

#     async def start(self) -> None:
#         """
#         전체 파이프라인 시작

#         모든 Stream 연결 함수를 병렬로 실행합니다.
#         """
#         if self._running:
#             logger.warning("[StreamPipeline] Pipeline이 이미 실행 중입니다")
#             return

#         self._running = True
#         logger.info("[StreamPipeline] Pipeline 시작")

#         try:
#             # 모든 연결 함수를 병렬로 실행
#             self._tasks = [
#                 asyncio.create_task(self._str_to_number()),
#                 asyncio.create_task(self._number_to_bytes()),
#                 asyncio.create_task(self._bytes_to_str()),
#             ]

#             # 모든 태스크 완료 대기
#             await asyncio.gather(*self._tasks, return_exceptions=True)

#             logger.info("[StreamPipeline] Pipeline 완료")

#         except Exception as e:
#             logger.error(
#                 f"[StreamPipeline] Pipeline 실행 중 오류: {str(e)}",
#                 exc_info=True,
#             )
#             raise
#         finally:
#             self._running = False

#     async def _str_to_number(self) -> None:
#         """
#         StrChannel → StrToNumberStream 연결

#         StrChannel에서 문자열을 받아 StrToNumberStream으로 전달합니다.
#         """
#         logger.info("[StreamPipeline] StrChannel → StrToNumberStream 연결 시작")

#         try:
#             async for text in self.str_channel.receive():
#                 await self.str_to_number_stream.send(text)
#                 logger.debug(
#                     f"[StreamPipeline] StrChannel → StrToNumberStream: text={text}"
#                 )

#         except Exception as e:
#             logger.error(
#                 f"[StreamPipeline] StrChannel → StrToNumberStream 연결 중 오류: {str(e)}",
#                 exc_info=True,
#             )
#             raise
#         finally:
#             await self.str_to_number_stream.close()
#             logger.info("[StreamPipeline] StrChannel → StrToNumberStream 연결 종료")

#     async def _number_to_bytes(self) -> None:
#         """
#         StrToNumberStream → NumberToBytesStream 연결

#         StrToNumberStream에서 숫자를 받아 NumberToBytesStream으로 전달합니다.
#         """
#         logger.info(
#             "[StreamPipeline] StrToNumberStream → NumberToBytesStream 연결 시작"
#         )

#         try:
#             async for number in self.str_to_number_stream.receive():
#                 await self.number_to_bytes_stream.send(number)
#                 logger.debug(
#                     f"[StreamPipeline] StrToNumberStream → NumberToBytesStream: number={number}"
#                 )

#         except Exception as e:
#             logger.error(
#                 f"[StreamPipeline] StrToNumberStream → NumberToBytesStream 연결 중 오류: {str(e)}",
#                 exc_info=True,
#             )
#             raise
#         finally:
#             await self.number_to_bytes_stream.close()
#             logger.info(
#                 "[StreamPipeline] StrToNumberStream → NumberToBytesStream 연결 종료"
#             )

#     async def _bytes_to_str(self) -> None:
#         """
#         NumberToBytesStream → BytesToStrStream 연결

#         NumberToBytesStream에서 bytes를 받아 BytesToStrStream으로 전달합니다.
#         """
#         logger.info("[StreamPipeline] NumberToBytesStream → BytesToStrStream 연결 시작")

#         try:
#             async for bytes_data in self.number_to_bytes_stream.receive():
#                 await self.bytes_to_str_stream.send(bytes_data)
#                 logger.debug(
#                     f"[StreamPipeline] NumberToBytesStream → BytesToStrStream: "
#                     f"size={len(bytes_data)} bytes"
#                 )

#         except Exception as e:
#             logger.error(
#                 f"[StreamPipeline] NumberToBytesStream → BytesToStrStream 연결 중 오류: {str(e)}",
#                 exc_info=True,
#             )
#             raise
#         finally:
#             await self.bytes_to_str_stream.close()
#             logger.info(
#                 "[StreamPipeline] NumberToBytesStream → BytesToStrStream 연결 종료"
#             )

#     async def close_all(self) -> None:
#         """
#         모든 Stream 종료

#         Pipeline의 모든 Stream을 안전하게 종료합니다.
#         """
#         logger.info("[StreamPipeline] 모든 Stream 종료 시작")

#         # 실행 중인 태스크 취소
#         if self._tasks:
#             for task in self._tasks:
#                 if not task.done():
#                     task.cancel()

#             # 태스크 완료 대기
#             try:
#                 await asyncio.gather(*self._tasks, return_exceptions=True)
#             except Exception as e:
#                 logger.warning(f"[StreamPipeline] 태스크 취소 중 오류: {str(e)}")

#         # 모든 Stream 종료
#         try:
#             await self.str_channel.close()
#         except Exception as e:
#             logger.warning(f"[StreamPipeline] StrChannel 종료 중 오류: {str(e)}")

#         try:
#             await self.str_to_number_stream.close()
#         except Exception as e:
#             logger.warning(f"[StreamPipeline] StrToNumberStream 종료 중 오류: {str(e)}")

#         try:
#             await self.number_to_bytes_stream.close()
#         except Exception as e:
#             logger.warning(
#                 f"[StreamPipeline] NumberToBytesStream 종료 중 오류: {str(e)}"
#             )

#         try:
#             await self.bytes_to_str_stream.close()
#         except Exception as e:
#             logger.warning(f"[StreamPipeline] BytesToStrStream 종료 중 오류: {str(e)}")

#         self._running = False
#         logger.info("[StreamPipeline] 모든 Stream 종료 완료")
