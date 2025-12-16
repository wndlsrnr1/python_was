"""
Daglo 실시간 STT 모듈

gRPC를 통한 실시간 음성 인식 기능을 제공합니다.
"""

# speech_pb2와 speech_pb2_grpc는 상대 import로 직접 노출
from . import speech_pb2
from . import speech_pb2_grpc
from .audio_adapter import (
    convert_to_linear16,
    convert_stream_to_linear16,
    get_supported_formats,
)

__all__ = [
    "speech_pb2",
    "speech_pb2_grpc",
    "convert_to_linear16",
    "convert_stream_to_linear16",
    "get_supported_formats",
]
