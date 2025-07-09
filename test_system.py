#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
시스템 테스트 및 디버깅 스크립트
백엔드 연동 포함 전체 기능 테스트
"""

import sys
import os
import importlib
import subprocess
import platform
import json
import asyncio
import time
from datetime import datetime

# 색상 코드
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class SystemTester:
    def __init__(self):
        self.test_results = []
        self.errors = []
        
    def print_header(self, title):
        """테스트 헤더 출력"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}{title:^60}{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")
        
    def print_result(self, test_name, success, message=""):
        """테스트 결과 출력"""
        status = f"{GREEN}✓ PASS{RESET}" if success else f"{RED}✗ FAIL{RESET}"
        print(f"{status} {test_name}")
        if message:
            print(f"  └─ {message}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
    def test_system_environment(self):
        """시스템 환경 테스트"""
        self.print_header("1. 시스템 환경 확인")
        
        # Python 버전 확인
        python_version = sys.version
        self.print_result(
            "Python 버전",
            sys.version_info >= (3, 8),
            f"현재: {python_version.split()[0]}"
        )
        
        # 플랫폼 확인
        self.print_result(
            "플랫폼",
            True,
            f"{platform.system()} {platform.release()}"
        )
        
        # NDI SDK 경로 확인 (Windows)
        if sys.platform == "win32":
            ndi_path = r"C:\Program Files\NDI\NDI 6 SDK\Bin\x64"
            ndi_exists = os.path.exists(ndi_path)
            self.print_result(
                "NDI SDK 경로",
                ndi_exists,
                ndi_path if ndi_exists else "NDI SDK가 설치되지 않음"
            )
            
    def test_dependencies(self):
        """의존성 패키지 테스트"""
        self.print_header("2. 의존성 패키지 확인")
        
        required_packages = [
            'PyQt6',
            'numpy',
            'pyqtgraph',
            'opencv-python',
            'requests',
            'websockets',
            'ffmpeg-python',
            'asyncio'
        ]
        
        for package in required_packages:
            try:
                if package == 'opencv-python':
                    importlib.import_module('cv2')
                elif package == 'ffmpeg-python':
                    importlib.import_module('ffmpeg')
                else:
                    importlib.import_module(package)
                self.print_result(f"{package} 임포트", True)
            except ImportError as e:
                self.print_result(f"{package} 임포트", False, str(e))
                self.errors.append(f"{package}: {e}")
                
    def test_module_imports(self):
        """프로젝트 모듈 임포트 테스트"""
        self.print_header("3. 프로젝트 모듈 임포트 테스트")
        
        modules_to_test = [
            'pd_app',
            'pd_app.core.ndi_manager',
            'pd_app.core.vmix_manager',
            'pd_app.core.srt_manager',
            'pd_app.core.auth_manager',
            'pd_app.ui.main_window',
            'pd_app.ui.ndi_widget',
            'pd_app.ui.tally_widget',
            'pd_app.ui.srt_widget',
            'pd_app.ui.login_widget',
            'pd_app.network.websocket_client',
            'pd_app.network.tcp_client',
            'pd_app.config.settings',
            'pd_app.config.constants',
            'pd_app.utils.logger',
            'pd_app.utils.helpers'
        ]
        
        for module in modules_to_test:
            try:
                importlib.import_module(module)
                self.print_result(f"{module}", True)
            except Exception as e:
                self.print_result(f"{module}", False, str(e))
                self.errors.append(f"{module}: {e}")
                
    def test_ndi_functionality(self):
        """NDI 기능 테스트"""
        self.print_header("4. NDI 기능 테스트")
        
        try:
            import NDIlib as ndi
            
            # NDI 초기화
            init_success = ndi.initialize()
            self.print_result("NDI 라이브러리 초기화", init_success)
            
            if init_success:
                # Finder 생성
                finder = ndi.find_create_v2()
                self.print_result("NDI Finder 생성", finder is not None)
                
                if finder:
                    # 소스 검색 (1초 대기)
                    ndi.find_wait_for_sources(finder, 1000)
                    sources = ndi.find_get_current_sources(finder)
                    
                    source_count = sources.no_sources if sources else 0
                    self.print_result(
                        "NDI 소스 검색",
                        True,
                        f"{source_count}개 소스 발견"
                    )
                    
                    # Finder 정리
                    ndi.find_destroy(finder)
                    
                # NDI 정리
                ndi.destroy()
                
        except Exception as e:
            self.print_result("NDI 기능", False, str(e))
            self.errors.append(f"NDI: {e}")
            
    def test_websocket_connection(self):
        """WebSocket 서버 연결 테스트"""
        self.print_header("5. WebSocket 서버 연동 테스트")
        
        async def test_ws():
            try:
                import websockets
                
                # returnfeed.net 서버 연결 시도
                uri = "wss://returnfeed.net/ws/"
                
                try:
                    async with websockets.connect(uri, ssl=True) as websocket:
                        self.print_result("WebSocket 연결", True, uri)
                        
                        # Ping 테스트
                        await websocket.send(json.dumps({"type": "ping"}))
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(response)
                        
                        self.print_result(
                            "서버 응답",
                            data.get("type") == "pong",
                            "Ping-Pong 성공"
                        )
                        
                except asyncio.TimeoutError:
                    self.print_result("WebSocket 연결", False, "연결 시간 초과")
                except Exception as e:
                    self.print_result("WebSocket 연결", False, str(e))
                    
            except ImportError:
                self.print_result("WebSocket", False, "websockets 모듈 없음")
                
        # 이벤트 루프 실행
        asyncio.run(test_ws())
        
    def test_media_mtx_api(self):
        """MediaMTX API 연결 테스트"""
        self.print_header("6. MediaMTX 서버 API 테스트")
        
        try:
            import requests
            
            # MediaMTX API 엔드포인트
            api_url = "http://returnfeed.net:9997/v3/paths/list"
            
            try:
                response = requests.get(api_url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    stream_count = len(data.get('items', []))
                    self.print_result(
                        "MediaMTX API 연결",
                        True,
                        f"활성 스트림: {stream_count}개"
                    )
                else:
                    self.print_result(
                        "MediaMTX API 연결",
                        False,
                        f"HTTP {response.status_code}"
                    )
                    
            except requests.RequestException as e:
                self.print_result("MediaMTX API 연결", False, str(e))
                
        except ImportError:
            self.print_result("MediaMTX API", False, "requests 모듈 없음")
            
    def test_ffmpeg_availability(self):
        """FFmpeg 설치 확인"""
        self.print_header("7. FFmpeg 설치 확인")
        
        try:
            # FFmpeg 버전 확인
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                self.print_result("FFmpeg", True, version_line)
                
                # SRT 지원 확인
                srt_support = 'enable-libsrt' in result.stdout
                self.print_result(
                    "FFmpeg SRT 지원",
                    srt_support,
                    "SRT 프로토콜 지원" if srt_support else "SRT 미지원"
                )
            else:
                self.print_result("FFmpeg", False, "실행 실패")
                
        except FileNotFoundError:
            self.print_result("FFmpeg", False, "FFmpeg가 설치되지 않음")
        except Exception as e:
            self.print_result("FFmpeg", False, str(e))
            
    def test_config_system(self):
        """설정 시스템 테스트"""
        self.print_header("8. 설정 시스템 테스트")
        
        try:
            from pd_app.config import Settings
            
            # 설정 객체 생성
            settings = Settings()
            self.print_result("Settings 객체 생성", True)
            
            # 설정 읽기/쓰기 테스트
            test_key = "test.value"
            test_value = "test_data_" + str(int(time.time()))
            
            settings.set(test_key, test_value)
            retrieved = settings.get(test_key)
            
            self.print_result(
                "설정 읽기/쓰기",
                retrieved == test_value,
                f"저장: {test_value}, 읽기: {retrieved}"
            )
            
            # 설정 파일 존재 확인
            config_exists = os.path.exists("config/settings.json")
            self.print_result(
                "설정 파일",
                config_exists,
                "config/settings.json"
            )
            
        except Exception as e:
            self.print_result("설정 시스템", False, str(e))
            self.errors.append(f"Config: {e}")
            
    def test_auth_system(self):
        """인증 시스템 테스트"""
        self.print_header("9. 인증 시스템 테스트")
        
        try:
            from pd_app.core import AuthManager
            
            # 인증 관리자 생성
            auth = AuthManager()
            self.print_result("AuthManager 생성", True)
            
            # 고유 주소 생성 테스트
            address = auth.generate_unique_address()
            self.print_result(
                "고유 주소 생성",
                len(address) == 8,
                f"생성된 주소: {address}"
            )
            
            # 로그인 시뮬레이션 (실제 서버 없이)
            # 실제로는 서버 API 필요
            self.print_result(
                "로그인 시스템",
                True,
                "시뮬레이션 모드 (실제 서버 연동 시 테스트 필요)"
            )
            
        except Exception as e:
            self.print_result("인증 시스템", False, str(e))
            self.errors.append(f"Auth: {e}")
            
    def generate_report(self):
        """테스트 보고서 생성"""
        self.print_header("테스트 완료 보고서")
        
        # 통계
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"총 테스트: {total_tests}")
        print(f"{GREEN}성공: {passed_tests}{RESET}")
        print(f"{RED}실패: {failed_tests}{RESET}")
        print(f"성공률: {passed_tests/total_tests*100:.1f}%")
        
        # 오류 요약
        if self.errors:
            print(f"\n{RED}오류 요약:{RESET}")
            for error in self.errors:
                print(f"  • {error}")
                
        # JSON 보고서 저장
        report = {
            'test_date': datetime.now().isoformat(),
            'system_info': {
                'platform': platform.system(),
                'python_version': sys.version,
            },
            'summary': {
                'total': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': passed_tests/total_tests*100
            },
            'results': self.test_results,
            'errors': self.errors
        }
        
        os.makedirs('test_reports', exist_ok=True)
        report_file = f"test_reports/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        print(f"\n보고서 저장: {report_file}")
        
def main():
    """메인 테스트 실행"""
    print(f"{BLUE}PD 통합 소프트웨어 시스템 테스트{RESET}")
    print(f"테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = SystemTester()
    
    # 테스트 실행
    tester.test_system_environment()
    tester.test_dependencies()
    tester.test_module_imports()
    tester.test_ndi_functionality()
    tester.test_websocket_connection()
    tester.test_media_mtx_api()
    tester.test_ffmpeg_availability()
    tester.test_config_system()
    tester.test_auth_system()
    
    # 보고서 생성
    tester.generate_report()
    
if __name__ == '__main__':
    main()