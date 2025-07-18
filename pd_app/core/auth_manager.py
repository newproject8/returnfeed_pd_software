# pd_app/core/auth_manager.py
"""
Authentication Manager - PD 로그인 및 고유 주소 시스템 관리
"""

import json
import uuid
import time
import hashlib
import logging
from datetime import datetime, timedelta

try:
    from PyQt6.QtCore import QObject, pyqtSignal
except ImportError:
    # Qt가 없는 환경에서도 기본 기능 사용 가능
    class QObject:
        pass
    class pyqtSignal:
        def __init__(self, *args):
            pass
        def emit(self, *args):
            pass

logger = logging.getLogger(__name__)

class AuthManager(QObject):
    """인증 관리자"""
    
    # 시그널 정의
    login_success = pyqtSignal(dict)
    login_failed = pyqtSignal(str)
    logout_success = pyqtSignal()
    token_expired = pyqtSignal()
    auth_state_changed = pyqtSignal(bool)  # 인증 상태 변경 시그널
    
    def __init__(self):
        super().__init__()
        self.user_info = None
        self.unique_address = None
        self.auth_token = None
        self.token_expiry = None
        
    def login(self, username, password):
        """PD 로그인 처리"""
        try:
            # TODO: 실제 서버 API 연동 구현
            # 현재는 시뮬레이션
            
            if not username or not password:
                self.login_failed.emit("사용자명과 비밀번호를 입력하세요")
                return False
                
            # 비밀번호 해시 (실제로는 서버에서 처리)
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # 시뮬레이션: 로그인 성공
            if username and password:  # 실제로는 서버 검증
                # 고유 주소 생성
                self.unique_address = self.generate_unique_address()
                
                # 사용자 정보 설정
                self.user_info = {
                    'user_id': username,
                    'username': username,
                    'unique_address': self.unique_address,
                    'login_time': datetime.now().isoformat()
                }
                
                # 토큰 생성 (실제로는 서버에서 JWT 발급)
                self.auth_token = self._generate_token(username)
                self.token_expiry = datetime.now() + timedelta(hours=24)
                
                self.login_success.emit(self.user_info)
                self.auth_state_changed.emit(True)  # 인증 상태 변경 알림
                logger.info(f"로그인 성공: {username} (주소: {self.unique_address})")
                return True
                
            else:
                self.login_failed.emit("잘못된 사용자명 또는 비밀번호")
                return False
                
        except Exception as e:
            error_msg = f"로그인 오류: {str(e)}"
            logger.error(error_msg)
            self.login_failed.emit(error_msg)
            return False
            
    def logout(self):
        """로그아웃 처리"""
        try:
            self.user_info = None
            self.unique_address = None
            self.auth_token = None
            self.token_expiry = None
            
            self.logout_success.emit()
            self.auth_state_changed.emit(False)  # 인증 상태 변경 알림
            logger.info("로그아웃 성공")
            
        except Exception as e:
            logger.error(f"로그아웃 오류: {e}")
            
    def generate_unique_address(self):
        """고유 주소 생성"""
        # UUID4 기반 8자리 고유 주소
        unique_id = str(uuid.uuid4())[:8].upper()
        return unique_id
        
    def regenerate_unique_address(self):
        """고유 주소 재생성"""
        if self.user_info:
            self.unique_address = self.generate_unique_address()
            self.user_info['unique_address'] = self.unique_address
            logger.info(f"고유 주소 재생성: {self.unique_address}")
            return self.unique_address
        return None
        
    def validate_token(self):
        """토큰 유효성 검증"""
        if not self.auth_token or not self.token_expiry:
            return False
            
        if datetime.now() > self.token_expiry:
            self.token_expired.emit()
            return False
            
        return True
        
    def refresh_token(self):
        """토큰 갱신"""
        if self.user_info and self.validate_token():
            # 토큰 갱신 (실제로는 서버 API 호출)
            self.token_expiry = datetime.now() + timedelta(hours=24)
            logger.info("토큰 갱신 성공")
            return True
        return False
        
    def _generate_token(self, username):
        """토큰 생성 (시뮬레이션)"""
        # 실제로는 서버에서 JWT 토큰 발급
        timestamp = str(int(time.time()))
        token_data = f"{username}:{timestamp}:{uuid.uuid4()}"
        return hashlib.sha256(token_data.encode()).hexdigest()
        
    def get_user_info(self):
        """현재 사용자 정보 반환"""
        return self.user_info
        
    def get_unique_address(self):
        """현재 고유 주소 반환"""
        return self.unique_address
        
    def is_logged_in(self):
        """로그인 상태 확인"""
        return self.user_info is not None and self.validate_token()
        
    def is_authenticated(self):
        """인증 상태 확인 (is_logged_in의 별칭)"""
        return self.is_logged_in()
        
    def get_username(self):
        """현재 사용자명 반환"""
        if self.user_info:
            return self.user_info.get('username', '')
        return ''
        
    def load_auth_info(self):
        """인증 정보 로드 (load_credentials의 별칭)"""
        return self.load_credentials()
        
    def save_credentials(self, auth_data=None, filepath="config/auth.json"):
        """인증 정보 저장 (선택사항)"""
        try:
            # auth_data가 dict로 전달된 경우 처리
            if isinstance(auth_data, dict):
                self.user_info = auth_data
                self.unique_address = auth_data.get('unique_address')
                if 'access_token' in auth_data:
                    self.auth_token = auth_data['access_token']
                
            # 저장할 데이터 준비
            save_data = {
                'user_info': self.user_info,
                'unique_address': self.unique_address,
                'token_expiry': self.token_expiry.isoformat() if self.token_expiry else None
            }
            
            # 디렉토리 생성
            import os
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(save_data, f)
                
            logger.info("인증 정보 저장 완료")
            
        except Exception as e:
            logger.error(f"인증 정보 저장 실패: {e}")
            
    def load_credentials(self, filepath="config/auth.json"):
        """저장된 인증 정보 로드 (선택사항)"""
        try:
            with open(filepath, 'r') as f:
                auth_data = json.load(f)
                
            self.user_info = auth_data.get('user_info')
            self.unique_address = auth_data.get('unique_address')
            
            if auth_data.get('token_expiry'):
                self.token_expiry = datetime.fromisoformat(auth_data['token_expiry'])
                
                # 토큰 유효성 확인
                if not self.validate_token():
                    self.logout()
                    return False
                    
            logger.info("인증 정보 로드 완료")
            return True
            
        except FileNotFoundError:
            logger.info("저장된 인증 정보 없음")
            return False
            
        except Exception as e:
            logger.error(f"인증 정보 로드 실패: {e}")
            return False