"""
모든 예제를 실행하는 테스트 스크립트

각 예제를 순차적으로 실행하고 결과를 출력합니다.
"""

import asyncio
import time
import importlib.util
from pathlib import Path


def run_example(module_name: str, file_path: Path) -> tuple[bool, float]:
    """예제 파일을 실행하고 결과를 반환
    
    Args:
        module_name: 모듈 이름
        file_path: 파일 경로
        
    Returns:
        (성공 여부, 실행 시간) 튜플
    """
    print(f"\n{'=' * 60}")
    print(f"실행 중: {file_path.name}")
    print('=' * 60)
    
    start_time = time.time()
    
    try:
        # 모듈 로드 및 실행
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            print(f"❌ 모듈 로드 실패: {file_path}")
            return False, 0.0
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # main 함수가 있으면 실행
        if hasattr(module, 'main'):
            if asyncio.iscoroutinefunction(module.main):
                asyncio.run(module.main())
            else:
                module.main()
        
        elapsed_time = time.time() - start_time
        print(f"\n✅ 성공: {file_path.name} (실행 시간: {elapsed_time:.2f}초)")
        return True, elapsed_time
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n❌ 실패: {file_path.name}")
        print(f"   오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, elapsed_time


def main():
    """모든 예제를 실행"""
    print("=" * 60)
    print("async for 및 AsyncIterator 튜토리얼 테스트")
    print("=" * 60)
    
    # 현재 디렉토리
    base_dir = Path(__file__).parent
    
    # 실행할 예제 파일 목록 (순서대로 실행)
    example_files = [
        ("00_why_async_for", base_dir / "00-why-async-for.py"),
        ("01_basic_async_for", base_dir / "01-basic-async-for.py"),
        ("02_async_iterator", base_dir / "02-async-iterator.py"),
        ("03_practical_example", base_dir / "03-practical-example.py"),
    ]
    
    results = []
    total_start_time = time.time()
    
    # 각 예제 실행
    for module_name, file_path in example_files:
        if not file_path.exists():
            print(f"\n⚠️  파일 없음: {file_path}")
            results.append((file_path.name, False, 0.0))
            continue
        
        success, elapsed_time = run_example(module_name, file_path)
        results.append((file_path.name, success, elapsed_time))
        
        # 예제 간 구분을 위한 대기
        print("\n" + "-" * 60)
        time.sleep(0.5)
    
    # 결과 요약
    total_time = time.time() - total_start_time
    
    print("\n" + "=" * 60)
    print("실행 결과 요약")
    print("=" * 60)
    
    success_count = sum(1 for _, success, _ in results if success)
    total_count = len(results)
    
    for filename, success, elapsed_time in results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{status}: {filename} ({elapsed_time:.2f}초)")
    
    print(f"\n총 {total_count}개 중 {success_count}개 성공")
    print(f"총 실행 시간: {total_time:.2f}초")
    
    if success_count == total_count:
        print("\n🎉 모든 예제가 성공적으로 실행되었습니다!")
    else:
        print(f"\n⚠️  {total_count - success_count}개 예제가 실패했습니다.")


if __name__ == "__main__":
    main()

