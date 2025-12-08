from watchdog.events import FileSystemEventHandler
import os
from datetime import datetime

class LoggingHandler(FileSystemEventHandler):
    """파일 변경을 로그로 기록하는 핸들러"""
    
    def __init__(self, log_file="file_changes.log"):
        self.log_file = log_file
    
    def _log(self, message):
        """로그 파일에 기록"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{log_message}\n")
        print(log_message)
    
    def on_created(self, event):
        if not event.is_directory:
            self._log(f"생성: {event.src_path}")
    
    def on_modified(self, event):
        if not event.is_directory:
            self._log(f"수정: {event.src_path}")
    
    def on_deleted(self, event):
        if not event.is_directory:
            self._log(f"삭제: {event.src_path}")
    
    def on_moved(self, event):
        self._log(f"이동: {event.src_path} -> {event.dest_path}")

