"""
오디오 형식 이해

오디오 형식의 구성 요소

오디포 파일은 다음 요소로 구성됩니다.

- 컨테이너 형식: 파일 포맷 (WebM, MP4, WAV 등)
- 오디오 코덱: 압축 알고리즘 (Opus, AAC, PCM 등)
- 샘플레이트: 초당 샘플 수 (Hz)
- 비트 깊이: 샘플당 비트 수
- 채널수: 모노(1), 스테레오(2)

WebM 형식

WebM은 웹에서 사용하기 위해 개발된 오픈 소스 컨테이너 형식입니다.

코덱 Opus, Vorbis 사용한다
높은 압축률
스트리밍에 적합
브라우저에서 네이티브 지원

용도: 웹 브라우저에서 녹음된 오디오

LINEAR16 PCM 형식

LINEAR16 PCM 은 압축되지 않은 원시 오디오 데이터입니다.

특징: 
    압축 없음 (원본 품질 유지)
    처리 속도가 빠름 
    파일 크기 큼
용도: STT 서버가 요구하는 표주 형식

형식 변환의 필요성

STT 서버는 특정 형식의 오디오를 요구합니다:
    - Daglo STT 서버 요구사항:
        - 형식: LINEAR16 PCM
        - 샘플레이트: 16000Hz
        - 채널: 모노 (1채널)
        - 비트 깊이: 16비트


스트리밍 변환 원리

배치 변환 vs 스트리밍 변환

배치 변환: 
    전체 파일을 메모리에 로드
    변환 후 결과 반환
    메모리 사용량 큼
    실시간 처리에 부적합

스트리밍 변환:
    청크 단위로 처리
    메모리 사용량 적음
    실시간 처리 가능
    지연 시간 최소화

ffmpeg를 이용한 변환

ffmpeg는 cpi 기반 오디오/비디오 변환 도구
-f signed 16-bit little-endian
-ar 16000
-ac 1
ffmpeg -i input.webm -f s16le -ar 16000 -ac 1 -acodec pcm_s16le output.raw

파이프를 이용한 스트리밍

stdin/stout 파이프를 이ㅛㅇ하면 파일 없이 스트리밍 변환이 가능합니다.

ffmpeg -i pipe:0 -f s16le -ar 16000 -ac 1 -acodec pcm_s16le pipe:1

stdin:
"""

class StreamAuydioConverter:


    def __init__(self, input_format: str = "webm"):
        self.input_format = input_format
        self.process = None
        self._closed = False
        