import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from collections import defaultdict


class DebouncedHandler(FileSystemEventHandler):
    """디바운싱을 사용한 핸들러"""

    def __init__(self, delay=1.0):
        self.delay = delay
        self.pending_events = defaultdict(list)
        self.lock = threading.Lock()

    def _process_event(self, file_path):
        """지연 후 이벤트 처리"""
        time.sleep(self.delay)
        with self.lock:
            if file_path in self.pending_events:
                print(f"[디바운싱] 파일 수정: {file_path}")
                del self.pending_events[file_path]

    def on_modified(self, event):
        if event.is_directory:
            return
        file_path = event.src_path
        with self.lock:
            if file_path not in self.pending_events:
                thread = threading.Thread(target=self._process_event, args=(file_path,))
                thread.daemon = True
                thread.start()
            self.pending_events[file_path].append(time.time())


if __name__ == "__main__":
    handler = DebouncedHandler(delay=1.0)
    observer = Observer()
    observer.schedule(handler, ".", recursive=False)
    observer.start()

    print("디바운싱 핸들러 시작 (1초 지연)")
    print("종료하려면 Ctrl+C를 누르세요.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n모니터링 종료")

    observer.join()
