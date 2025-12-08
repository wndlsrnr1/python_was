import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MyHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        """모든 이벤트를 처리"""
        if event.is_directory:
            print(f"[디렉토리] {event.event_type}: {event.src_path}")
        else:
            print(f"[파일] {event.event_type}: {event.src_path}")

if __name__ == "__main__":
    # 모니터링할 디렉토리
    watch_directory = "."

    # 이벤트 핸들러 생성
    event_handler = MyHandler()

    # 옵저버 생성 (재귀적 모니터링)
    observer = Observer()
    observer.schedule(event_handler, watch_directory, recursive=True)

    # 모니터링 시작
    observer.start()
    print(f"재귀적 모니터링 시작: {watch_directory}")
    print("종료하려면 Ctrl+C를 누르세요.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n모니터링 종료")

    observer.join()

