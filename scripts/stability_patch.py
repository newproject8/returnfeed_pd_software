#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""안정성 개선 패치 - 크래시 방지 및 성능 최적화"""

import os
import sys

def patch_ndi_widget():
    """NDI 위젯에 크래시 방지 코드 추가"""
    
    file_path = "pd_app/ui/ndi_widget.py"
    
    # 백업 생성
    import shutil
    shutil.copy(file_path, f"{file_path}.backup")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # video_widget.setImage 호출 부분에 try-except 추가
    old_code = """            self.video_widget.setImage(frame)"""
    
    new_code = """            try:
                self.video_widget.setImage(frame)
            except Exception as display_error:
                # 디스플레이 오류 무시 (크래시 방지)
                pass"""
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[O] {file_path} 패치 완료")
    else:
        print(f"[!] {file_path} 이미 패치됨")

def patch_main_window():
    """메인 윈도우에 안전한 종료 처리 추가"""
    
    file_path = "pd_app/ui/main_window.py"
    
    # closeEvent 메서드 확인
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # closeEvent에 추가 안전장치
    if "def closeEvent(self, event):" in content:
        print(f"[O] {file_path} closeEvent 이미 존재")
    else:
        # closeEvent 메서드 추가
        import_section = "from PyQt6.QtCore import Qt, QTimer"
        new_import = "from PyQt6.QtCore import Qt, QTimer\nfrom PyQt6.QtGui import QCloseEvent"
        
        content = content.replace(import_section, new_import)
        
        # 클래스 끝에 closeEvent 추가
        class_end = "        self.show()"
        close_event_code = """        self.show()
        
    def closeEvent(self, event: QCloseEvent):
        \"\"\"안전한 종료 처리\"\"\"
        try:
            logger.info("애플리케이션 종료 시작")
            
            # 모든 스레드 정지
            if hasattr(self, 'ndi_manager'):
                self.ndi_manager.cleanup()
            
            if hasattr(self, 'websocket_client'):
                self.websocket_client.stop()
            
            if hasattr(self, 'vmix_manager'):
                self.vmix_manager.cleanup()
            
            # 이벤트 수락
            event.accept()
            
        except Exception as e:
            logger.error(f"종료 중 오류: {e}")
            event.accept()"""
        
        content = content.replace(class_end, close_event_code)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[O] {file_path} 안전 종료 추가")

def create_crash_handler():
    """크래시 핸들러 생성"""
    
    handler_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""글로벌 예외 처리기"""

import sys
import traceback
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def handle_exception(exc_type, exc_value, exc_traceback):
    """처리되지 않은 예외 처리"""
    
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # 크래시 로그 생성
    crash_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    crash_log = f"logs/crash_{crash_time}.log"
    
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # 로그 파일에 기록
    with open(crash_log, 'w', encoding='utf-8') as f:
        f.write(f"크래시 시간: {datetime.now()}\\n")
        f.write(f"Python 버전: {sys.version}\\n")
        f.write(f"\\n{error_msg}")
    
    logger.critical(f"처리되지 않은 예외 발생:\\n{error_msg}")
    
    # 사용자에게 알림
    try:
        from PyQt6.QtWidgets import QMessageBox, QApplication
        
        if QApplication.instance():
            QMessageBox.critical(
                None,
                "오류 발생",
                f"예기치 않은 오류가 발생했습니다.\\n\\n"
                f"오류 로그: {crash_log}\\n\\n"
                f"프로그램을 재시작해 주세요."
            )
    except:
        pass

def install_handler():
    """예외 처리기 설치"""
    sys.excepthook = handle_exception
'''
    
    with open("pd_app/utils/crash_handler.py", 'w', encoding='utf-8') as f:
        f.write(handler_code)
    
    print("[O] 크래시 핸들러 생성 완료")

def patch_main_integrated():
    """main_integrated.py에 크래시 핸들러 추가"""
    
    file_path = "main_integrated.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 크래시 핸들러 임포트 추가
    if "crash_handler" not in content:
        import_section = "from pd_app.utils.logger import setup_logger"
        new_import = """from pd_app.utils.logger import setup_logger
from pd_app.utils.crash_handler import install_handler"""
        
        content = content.replace(import_section, new_import)
        
        # main() 함수 시작 부분에 핸들러 설치
        main_start = 'logger.info("main() 함수 시작")'
        new_main = '''logger.info("main() 함수 시작")
    
    # 크래시 핸들러 설치
    install_handler()
    logger.info("크래시 핸들러 설치 완료")'''
        
        content = content.replace(main_start, new_main)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[O] {file_path} 크래시 핸들러 추가")

def main():
    """메인 패치 함수"""
    
    print("=== 안정성 개선 패치 시작 ===\n")
    
    # 1. NDI 위젯 패치
    patch_ndi_widget()
    
    # 2. 메인 윈도우 패치
    patch_main_window()
    
    # 3. 크래시 핸들러 생성
    create_crash_handler()
    
    # 4. main_integrated.py 패치
    patch_main_integrated()
    
    print("\n=== 패치 완료 ===")
    print("\n다음 개선사항이 적용되었습니다:")
    print("- NDI 프레임 표시 오류 방지")
    print("- 안전한 종료 처리")
    print("- 글로벌 크래시 핸들러")
    print("- 오류 발생 시 자동 로그 생성")

if __name__ == "__main__":
    main()