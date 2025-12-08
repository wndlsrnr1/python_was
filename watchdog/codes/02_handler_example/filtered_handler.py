from watchdog.events import FileSystemEventHandler

class PythonFileHandler(FileSystemEventHandler):
    """Python 파일만 감시하는 핸들러"""
    
    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.py'):
            print(f"Python 파일 수정: {event.src_path}")
    
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.py'):
            print(f"Python 파일 생성: {event.src_path}")
    
    def on_deleted(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.py'):
            print(f"Python 파일 삭제: {event.src_path}")

