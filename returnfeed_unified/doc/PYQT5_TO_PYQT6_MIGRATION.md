# PyQt5 to PyQt6 Migration Guide

## vMix 모듈 마이그레이션 체크리스트

### 1. Import 변경
```python
# PyQt5
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit
from PyQt5.QtCore import pyqtSignal, QObject, QThread, Qt
from PyQt5.QtGui import QFont

# PyQt6
from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit
from PyQt6.QtCore import pyqtSignal, QObject, QThread, Qt
from PyQt6.QtGui import QFont
```

### 2. Qt 네임스페이스 변경
```python
# PyQt5
Qt.AlignCenter

# PyQt6  
Qt.AlignmentFlag.AlignCenter
```

### 3. exec_() → exec() 변경
```python
# PyQt5
app.exec_()

# PyQt6
app.exec()
```

### 4. 주요 변경사항
- QRegExp → QRegularExpression
- Qt.MidButton → Qt.MouseButton.MiddleButton
- QAction이 QtGui에서 QtWidgets로 이동

### 5. 시그널 연결 변경사항
- 대부분 동일하게 작동
- 일부 deprecated 시그널 확인 필요

## 모듈별 변경 필요 항목

### vMix_tcp_tally2.py
1. Line 23-27: PyQt5 imports → PyQt6
2. Line 227: Qt.AlignCenter → Qt.AlignmentFlag.AlignCenter
3. Line 345: app.exec_() → app.exec()

### 통합 시 고려사항
1. 두 모듈 모두 PyQt6로 통일
2. 공통 UI 컴포넌트는 PyQt6 기반으로 작성
3. 스타일시트는 대부분 호환됨