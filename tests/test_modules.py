#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
모듈별 단위 테스트
각 관리자 클래스의 기능을 개별 테스트
"""

import unittest
import sys
import os
import json
import time
from unittest.mock import Mock, patch, MagicMock

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 테스트할 모듈 임포트
from pd_app.core.auth_manager import AuthManager
from pd_app.core.srt_manager import SRTManager, MediaMTXClient
from pd_app.config.settings import Settings
from pd_app.utils.helpers import truncate_text, format_bytes, format_duration

class TestAuthManager(unittest.TestCase):
    """인증 관리자 테스트"""
    
    def setUp(self):
        self.auth_manager = AuthManager()
        
    def test_generate_unique_address(self):
        """고유 주소 생성 테스트"""
        address = self.auth_manager.generate_unique_address()
        self.assertEqual(len(address), 8)
        self.assertTrue(address.isupper())
        
        # 고유성 테스트
        addresses = set()
        for _ in range(100):
            addr = self.auth_manager.generate_unique_address()
            addresses.add(addr)
        self.assertEqual(len(addresses), 100)  # 모두 고유해야 함
        
    def test_login_simulation(self):
        """로그인 시뮬레이션 테스트"""
        # 로그인 시도
        success = self.auth_manager.login("test_user", "test_pass")
        self.assertTrue(success)
        
        # 로그인 상태 확인
        self.assertTrue(self.auth_manager.is_logged_in())
        self.assertIsNotNone(self.auth_manager.user_info)
        self.assertIsNotNone(self.auth_manager.unique_address)
        
    def test_logout(self):
        """로그아웃 테스트"""
        # 로그인 후 로그아웃
        self.auth_manager.login("test_user", "test_pass")
        self.auth_manager.logout()
        
        # 상태 확인
        self.assertFalse(self.auth_manager.is_logged_in())
        self.assertIsNone(self.auth_manager.user_info)
        self.assertIsNone(self.auth_manager.unique_address)
        
class TestMediaMTXClient(unittest.TestCase):
    """MediaMTX 클라이언트 테스트"""
    
    def setUp(self):
        self.client = MediaMTXClient("test.server", 8890, 9997)
        
    def test_publish_stream_url(self):
        """스트림 퍼블리시 URL 생성 테스트"""
        # 기본 URL
        url = self.client.publish_stream("test_stream")
        self.assertEqual(url, "srt://test.server:8890?streamid=publish:test_stream&pkt_size=1316")
        
        # 인증 포함 URL
        url = self.client.publish_stream("test_stream", "user", "pass")
        self.assertEqual(url, "srt://test.server:8890?streamid=publish:test_stream:user:pass&pkt_size=1316")
        
    def test_consume_stream_url(self):
        """스트림 소비 URL 생성 테스트"""
        url = self.client.consume_stream("test_stream")
        self.assertEqual(url, "srt://test.server:8890?streamid=read:test_stream")
        
class TestSRTManager(unittest.TestCase):
    """SRT 관리자 테스트"""
    
    def setUp(self):
        self.srt_manager = SRTManager()
        
    def test_generate_stream_key(self):
        """스트림 키 생성 테스트"""
        key = self.srt_manager.generate_stream_key("user123", "ABCD1234")
        
        # 형식 확인: user_id_unique_address_timestamp
        parts = key.split('_')
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "user123")
        self.assertEqual(parts[1], "ABCD1234")
        self.assertTrue(parts[2].isdigit())
        
    def test_stream_info(self):
        """스트림 정보 조회 테스트"""
        info = self.srt_manager.get_stream_info()
        
        self.assertIn('is_streaming', info)
        self.assertIn('stream_name', info)
        self.assertIn('server', info)
        self.assertIn('srt_port', info)
        
        self.assertFalse(info['is_streaming'])
        self.assertIsNone(info['stream_name'])
        
class TestSettings(unittest.TestCase):
    """설정 관리자 테스트"""
    
    def setUp(self):
        # 테스트용 임시 설정 파일 사용
        self.test_config_file = "test_config.json"
        self.settings = Settings()
        self.settings.config_file = self.test_config_file
        
    def tearDown(self):
        # 테스트 파일 정리
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
            
    def test_get_set_config(self):
        """설정 읽기/쓰기 테스트"""
        # 설정 쓰기
        self.settings.set('test.key', 'test_value')
        
        # 설정 읽기
        value = self.settings.get('test.key')
        self.assertEqual(value, 'test_value')
        
        # 중첩된 설정
        self.settings.set('test.nested.value', 123)
        value = self.settings.get('test.nested.value')
        self.assertEqual(value, 123)
        
    def test_default_config(self):
        """기본 설정 테스트"""
        server_config = self.settings.get_server_config()
        self.assertIn('websocket_url', server_config)
        self.assertIn('media_mtx_server', server_config)
        
        vmix_config = self.settings.get_vmix_config()
        self.assertIn('default_ip', vmix_config)
        self.assertIn('default_http_port', vmix_config)
        
class TestHelpers(unittest.TestCase):
    """헬퍼 함수 테스트"""
    
    def test_truncate_text(self):
        """텍스트 자르기 테스트"""
        self.assertEqual(truncate_text("short", 10), "short")
        self.assertEqual(truncate_text("very long text here", 10), "very lo...")
        self.assertEqual(truncate_text(None), "")
        
    def test_format_bytes(self):
        """바이트 포맷 테스트"""
        self.assertEqual(format_bytes(100), "100.00 B")
        self.assertEqual(format_bytes(1024), "1.00 KB")
        self.assertEqual(format_bytes(1024 * 1024), "1.00 MB")
        self.assertEqual(format_bytes(1024 * 1024 * 1024), "1.00 GB")
        
    def test_format_duration(self):
        """시간 포맷 테스트"""
        self.assertEqual(format_duration(30), "00:30")
        self.assertEqual(format_duration(90), "01:30")
        self.assertEqual(format_duration(3661), "01:01:01")
        
class TestIntegration(unittest.TestCase):
    """통합 테스트"""
    
    def test_auth_and_stream_key_integration(self):
        """인증과 스트림 키 생성 통합 테스트"""
        # 인증 관리자와 SRT 관리자 생성
        auth_manager = AuthManager()
        srt_manager = SRTManager()
        
        # 로그인
        auth_manager.login("test_user", "password")
        user_info = auth_manager.get_user_info()
        
        # 스트림 키 생성
        stream_key = srt_manager.generate_stream_key(
            user_info['user_id'],
            user_info['unique_address']
        )
        
        # 형식 확인
        self.assertIn(user_info['user_id'], stream_key)
        self.assertIn(user_info['unique_address'], stream_key)
        
    def test_config_persistence(self):
        """설정 지속성 테스트"""
        settings1 = Settings()
        settings1.config_file = "test_persist.json"
        
        # 설정 저장
        settings1.set('user.name', 'test_user')
        settings1.set('user.address', 'ABCD1234')
        settings1.save_config()
        
        # 새 인스턴스로 로드
        settings2 = Settings()
        settings2.config_file = "test_persist.json"
        settings2.load_config()
        
        # 값 확인
        self.assertEqual(settings2.get('user.name'), 'test_user')
        self.assertEqual(settings2.get('user.address'), 'ABCD1234')
        
        # 정리
        if os.path.exists("test_persist.json"):
            os.remove("test_persist.json")

def run_tests():
    """테스트 실행"""
    # 테스트 스위트 생성
    suite = unittest.TestSuite()
    
    # 테스트 추가
    test_classes = [
        TestAuthManager,
        TestMediaMTXClient,
        TestSRTManager,
        TestSettings,
        TestHelpers,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
        
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 결과 요약
    print(f"\n테스트 완료: {result.testsRun}개")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"실패: {len(result.failures)}")
    print(f"오류: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)