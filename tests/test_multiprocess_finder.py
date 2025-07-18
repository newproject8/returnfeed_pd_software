import multiprocessing
import os
import sys

def test_finder():
    """별도 프로세스에서 Finder 생성 테스트"""
    try:
        # NDI DLL 경로 추가
        ndi_dll_path = r"C:\Program Files\NDI\NDI 6 SDK\Bin\x64"
        if hasattr(os, 'add_dll_directory') and os.path.isdir(ndi_dll_path):
            os.add_dll_directory(ndi_dll_path)
            print(f"DLL 경로 추가됨: {ndi_dll_path}")
        
        # Finder 생성 시도
        from cyndilib.finder import Finder
        print("Finder 클래스 임포트 성공")
        
        finder = Finder()
        print(f"Finder 생성 결과: {finder is not None}")
        print(f"Finder 객체 타입: {type(finder)}")
        print(f"Finder 객체 값: {finder}")
        
        # Finder 객체의 메서드 확인
        if hasattr(finder, 'get_sources'):
            print("get_sources 메서드 존재")
        else:
            print("get_sources 메서드 없음")
            
        # cyndilib 초기화 상태 확인
        try:
            import cyndilib
            print(f"cyndilib 버전: {cyndilib.get_ndi_version()}")
        except Exception as e:
            print(f"cyndilib 버전 확인 실패: {e}")
        
        if finder is not None:
            print("Finder 객체 생성 성공")
            return True
        else:
            print("Finder 객체 생성 실패 (None 반환)")
            return False
            
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("메인 프로세스에서 Finder 테스트:")
    main_result = test_finder()
    print(f"메인 프로세스 결과: {main_result}")
    
    print("\n별도 프로세스에서 Finder 테스트:")
    multiprocessing.set_start_method('spawn', force=True)
    
    with multiprocessing.Pool(1) as pool:
        try:
            result = pool.apply(test_finder)
            print(f"별도 프로세스 결과: {result}")
        except Exception as e:
            print(f"멀티프로세싱 오류: {str(e)}")
            import traceback
            traceback.print_exc()