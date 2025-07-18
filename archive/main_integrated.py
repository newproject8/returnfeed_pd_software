#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PD 통합 소프트웨어 - 메인 실행 파일
NDI 프리뷰, vMix Tally, SRT 스트리밍 통합 시스템
"""

import sys
import os
import logging
import locale
import io

# Windows 한글 인코딩 설정
if sys.platform == "win32":
    try:
        # UTF-8 출력 설정
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        # Windows 콘솔 코드 페이지를 UTF-8로 설정
        os.system('chcp 65001 > nul')
    except:
        pass

# 로거를 가장 먼저 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pd_app.utils import setup_logger
logger = setup_logger()

logger.info("="*80)
logger.info("PD 통합 소프트웨어 시작")
logger.info("="*80)

# NDI DLL 경로 추가 (Windows)
if sys.platform == "win32":
    NDI_SDK_DLL_PATH = r"C:\Program Files\NDI\NDI 6 SDK\Bin\x64"
    logger.info(f"Windows 환경 감지 - NDI SDK 경로 확인: {NDI_SDK_DLL_PATH}")
    
    if hasattr(os, 'add_dll_directory'):
        if os.path.isdir(NDI_SDK_DLL_PATH):
            try:
                os.add_dll_directory(NDI_SDK_DLL_PATH)
                logger.info(f"NDI SDK DLL 경로 추가 성공: {NDI_SDK_DLL_PATH}")
            except Exception as e:
                logger.error(f"NDI SDK DLL 경로 추가 실패: {e}", exc_info=True)
        else:
            logger.warning(f"NDI SDK 경로가 존재하지 않음: {NDI_SDK_DLL_PATH}")
    else:
        logger.warning("Python 3.8 미만 버전 - add_dll_directory 사용 불가")

# PyQt6 임포트
try:
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtCore import Qt
    from PyQt6.QtCore import Qt
    logger.info("PyQt6 임포트 성공")
except ImportError as e:
    logger.critical(f"PyQt6 임포트 실패: {e}", exc_info=True)
    sys.exit(1)

# NDI 라이브러리 초기화 테스트
ndi_available = False
try:
    import NDIlib as ndi
    logger.info("NDIlib 모듈 임포트 성공")
    if not ndi.initialize():
        raise RuntimeError("NDIlib 초기화 실패")
    logger.info("NDIlib 초기화 성공")
    ndi_available = True
except ImportError as e:
    logger.warning(f"NDIlib를 찾을 수 없음 - 시뮬레이터 모드로 실행: {e}")
except Exception as e:
    logger.error(f"NDI 초기화 오류: {e}", exc_info=True)

# 메인 윈도우 임포트
try:
    from pd_app.ui import MainWindow
    from pd_app.config import Settings
    from pd_app.utils.helpers import get_platform_info
    logger.info("PD 앱 모듈 임포트 성공")
except ImportError as e:
    logger.critical(f"PD 앱 모듈 임포트 실패: {e}", exc_info=True)
    sys.exit(1)

def show_error_dialog(title, message):
    """오류 대화상자 표시"""
    try:
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        # GUI 성능 최적화 - PyQt6 호환
        # PyQt6에서는 High DPI가 기본적으로 활성화되어 있음
        # AA_UseHighDpiPixmaps와 AA_EnableHighDpiScaling은 제거됨
        try:
            app.setAttribute(Qt.ApplicationAttribute.AA_CompressHighFrequencyEvents, True)
        except AttributeError:
            logger.warning("AA_CompressHighFrequencyEvents 속성이 없습니다 - PyQt6 기본값 사용")
        QMessageBox.critical(None, title, message)
    except Exception as e:
        logger.error(f"오류 대화상자 표시 실패: {e}", exc_info=True)
        print(f"\n[오류] {title}: {message}\n")

def main():
    """메인 함수"""
    logger.info("main() 함수 시작")
    
    # 크래시 핸들러 설치
    try:
        from pd_app.utils.crash_handler import install_handler
        install_handler()
        logger.info("크래시 핸들러 설치 완료")
    except ImportError:
        logger.warning("크래시 핸들러를 로드할 수 없습니다")
    except Exception as e:
        logger.warning(f"크래시 핸들러 설치 실패: {e}")
    
    try:
        # 플랫폼 정보 로깅
        try:
            platform_info = get_platform_info()
            logger.info(f"플랫폼 정보: {platform_info}")
        except Exception as e:
            logger.error(f"플랫폼 정보 수집 오류: {e}", exc_info=True)
        
        # 고DPI 스케일링 설정 (PyQt6에서는 기본적으로 활성화됨)
        # PyQt5에서만 필요한 설정이므로 PyQt6에서는 건너뜀
        try:
            # Qt6에서는 이미 High DPI가 기본 활성화되어 있음
            if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
                QApplication.setHighDpiScaleFactorRoundingPolicy(
                    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
                )
        except Exception as e:
            logger.debug(f"High DPI 설정 건너뜀: {e}")
        
        # Qt 애플리케이션 생성
        logger.info("Qt 애플리케이션 생성 시작")
        app = QApplication(sys.argv)
        
        # GUI 성능 최적화 - PyQt6 호환
        # PyQt6에서는 High DPI가 기본적으로 활성화되어 있음
        # AA_UseHighDpiPixmaps와 AA_EnableHighDpiScaling은 제거됨
        try:
            app.setAttribute(Qt.ApplicationAttribute.AA_CompressHighFrequencyEvents, True)
            app.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
        except AttributeError:
            logger.warning("일부 Qt 속성이 없습니다 - PyQt6 기본값 사용")
        
        # 스타일 설정으로 부드러운 UI
        app.setStyle('Fusion')
        
        app.setApplicationName("PD 통합 소프트웨어")
        app.setOrganizationName("PD Software Team")
        logger.info("Qt 애플리케이션 생성 완료")
        
        # 설정 로드
        logger.info("설정 파일 로드 시작")
        try:
            settings = Settings()
            logger.info("설정 파일 로드 성공")
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}", exc_info=True)
            settings = None
        
        # 메인 윈도우 생성
        logger.info("메인 윈도우 생성 시작")
        try:
            main_window = MainWindow()
            
            # 윈도우 최적화 설정
            main_window.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
            main_window.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
            
            logger.info("메인 윈도우 생성 성공")
        except Exception as e:
            logger.critical(f"메인 윈도우 생성 실패: {e}", exc_info=True)
            show_error_dialog("치명적 오류", f"메인 윈도우 생성 중 오류가 발생했습니다:\n{e}")
            return
        
        # 저장된 윈도우 위치/크기 복원
        geometry_str = settings.get('ui.window_geometry')
        if geometry_str:
            try:
                import base64
                from PyQt6.QtCore import QByteArray
                geometry_data = base64.b64decode(geometry_str)
                geometry = QByteArray(geometry_data)
                main_window.restoreGeometry(geometry)
            except Exception as e:
                logger.debug(f"윈도우 geometry 복원 실패: {e}")
        
        # 마지막 탭 복원
        last_tab = settings.get('ui.last_tab', 0)
        main_window.tab_widget.setCurrentIndex(last_tab)
        
        # 윈도우 표시
        main_window.show()
        
        logger.info("애플리케이션 시작 완료")
        
        # 이벤트 루프 실행
        exit_code = app.exec()
        
        # 종료 시 설정 저장
        settings.update_window_geometry(main_window.saveGeometry())
        settings.update_last_tab(main_window.tab_widget.currentIndex())
        
        # NDI 정리
        try:
            # ndi가 임포트되어 있는지 확인
            if 'ndi' in locals() or 'ndi' in globals():
                ndi.destroy()
                logger.info("NDI 정리 완료")
        except Exception as e:
            logger.debug(f"NDI 정리 건너뜀: {e}")
            
        logger.info("애플리케이션 정상 종료")
        sys.exit(exit_code)
        
    except Exception as e:
        logger.critical(f"치명적 오류: {type(e).__name__}: {e}", exc_info=True)
        error_msg = f"애플리케이션 실행 중 오류가 발생했습니다:\n\n{type(e).__name__}: {e}\n\n자세한 내용은 로그 파일을 확인하세요."
        show_error_dialog("치명적 오류", error_msg)
        sys.exit(1)

if __name__ == '__main__':
    main()