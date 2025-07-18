# pd_app/ui/login_widget.py
"""
Login Widget - PD 로그인 및 고유 주소 관리 UI
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

class LoginWidget(QWidget):
    """로그인 위젯"""
    
    # 시그널 정의
    login_success = pyqtSignal()
    logout_success = pyqtSignal()
    
    def __init__(self, auth_manager):
        super().__init__()
        self.auth_manager = auth_manager
        self.init_ui()
        self.init_connections()
        
        # 저장된 인증 정보 로드 시도
        self.auth_manager.load_credentials()
        self.update_login_status()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 로그인 그룹
        login_group = QGroupBox("PD 로그인")
        login_layout = QVBoxLayout()
        
        # 사용자명
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("사용자명:"))
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("사용자명을 입력하세요")
        username_layout.addWidget(self.username_input)
        
        login_layout.addLayout(username_layout)
        
        # 비밀번호
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("비밀번호:"))
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("비밀번호를 입력하세요")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(self.password_input)
        
        login_layout.addLayout(password_layout)
        
        # 로그인 버튼
        button_layout = QHBoxLayout()
        
        self.login_button = QPushButton("로그인")
        button_layout.addWidget(self.login_button)
        
        self.logout_button = QPushButton("로그아웃")
        self.logout_button.setEnabled(False)
        button_layout.addWidget(self.logout_button)
        
        login_layout.addLayout(button_layout)
        
        login_group.setLayout(login_layout)
        layout.addWidget(login_group)
        
        # 고유 주소 그룹
        address_group = QGroupBox("고유 주소 관리")
        address_layout = QVBoxLayout()
        
        # 현재 고유 주소
        current_address_layout = QHBoxLayout()
        current_address_layout.addWidget(QLabel("현재 주소:"))
        
        self.address_label = QLabel("-")
        self.address_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        current_address_layout.addWidget(self.address_label)
        
        current_address_layout.addStretch()
        
        self.regenerate_button = QPushButton("재생성")
        self.regenerate_button.setEnabled(False)
        current_address_layout.addWidget(self.regenerate_button)
        
        address_layout.addLayout(current_address_layout)
        
        # 주소 설명
        info_label = QLabel(
            "고유 주소는 스트리밍 및 서버 통신에 사용됩니다.\n"
            "다른 사용자와 중복되지 않는 고유한 식별자입니다."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666;")
        address_layout.addWidget(info_label)
        
        address_group.setLayout(address_layout)
        layout.addWidget(address_group)
        
        # 로그인 상태
        status_group = QGroupBox("로그인 상태")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("로그인되지 않음")
        status_layout.addWidget(self.status_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        layout.addStretch()
        
    def init_connections(self):
        """시그널 연결"""
        # 인증 관리자 시그널
        self.auth_manager.login_success.connect(self.on_login_success)
        self.auth_manager.login_failed.connect(self.on_login_failed)
        self.auth_manager.logout_success.connect(self.on_logout_success)
        
        # UI 시그널
        self.login_button.clicked.connect(self.login)
        self.logout_button.clicked.connect(self.logout)
        self.regenerate_button.clicked.connect(self.regenerate_address)
        
        # 엔터키 처리
        self.username_input.returnPressed.connect(self.login)
        self.password_input.returnPressed.connect(self.login)
        
    def login(self):
        """로그인 처리"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "입력 오류", "사용자명과 비밀번호를 모두 입력하세요.")
            return
            
        # 로그인 시도
        self.login_button.setEnabled(False)
        self.auth_manager.login(username, password)
        
    def logout(self):
        """로그아웃 처리"""
        reply = QMessageBox.question(
            self,
            "로그아웃 확인",
            "로그아웃하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.auth_manager.logout()
            
    def regenerate_address(self):
        """고유 주소 재생성"""
        reply = QMessageBox.question(
            self,
            "주소 재생성 확인",
            "고유 주소를 재생성하시겠습니까?\n"
            "기존 주소로 연결된 서비스는 재연결이 필요합니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            new_address = self.auth_manager.regenerate_unique_address()
            if new_address:
                self.address_label.setText(new_address)
                QMessageBox.information(
                    self,
                    "주소 재생성 완료",
                    f"새로운 고유 주소: {new_address}"
                )
                
    def on_login_success(self, user_info):
        """로그인 성공"""
        self.update_login_status()
        QMessageBox.information(
            self,
            "로그인 성공",
            f"환영합니다, {user_info['username']}님!\n"
            f"고유 주소: {user_info['unique_address']}"
        )
        
        # 인증 정보 저장
        self.auth_manager.save_credentials()
        
        # 상위 위젯에 알림
        self.login_success.emit()
        
    def on_login_failed(self, error):
        """로그인 실패"""
        self.login_button.setEnabled(True)
        QMessageBox.critical(self, "로그인 실패", error)
        
    def on_logout_success(self):
        """로그아웃 성공"""
        self.update_login_status()
        QMessageBox.information(self, "로그아웃", "로그아웃되었습니다.")
        
        # 상위 위젯에 알림
        self.logout_success.emit()
        
    def update_login_status(self):
        """로그인 상태 업데이트"""
        if self.auth_manager.is_logged_in():
            user_info = self.auth_manager.get_user_info()
            
            # UI 업데이트
            self.username_input.setText(user_info['username'])
            self.username_input.setEnabled(False)
            self.password_input.clear()
            self.password_input.setEnabled(False)
            
            self.login_button.setEnabled(False)
            self.logout_button.setEnabled(True)
            
            self.address_label.setText(user_info['unique_address'])
            self.regenerate_button.setEnabled(True)
            
            self.status_label.setText(
                f"로그인됨: {user_info['username']}\n"
                f"로그인 시간: {user_info['login_time']}"
            )
            
        else:
            # UI 초기화
            self.username_input.clear()
            self.username_input.setEnabled(True)
            self.password_input.clear()
            self.password_input.setEnabled(True)
            
            self.login_button.setEnabled(True)
            self.logout_button.setEnabled(False)
            
            self.address_label.setText("-")
            self.regenerate_button.setEnabled(False)
            
            self.status_label.setText("로그인되지 않음")