# 변경 사항 (2025-07-16)

## 주요 성과

### 🚀 성능 최적화
- **프록시 모드 60fps 달성**: Non-blocking timeout (0ms) 적용으로 40fps → 60fps
- **CPU 사용률 30% 감소**: 프록시 모드 최적화로 10-15% 수준 달성
- **프레임 페이싱 제거**: 불필요한 msleep() 제거로 실시간성 향상

### 🎨 UI/UX 개선
- **모던 토글 스위치**: 프록시/일반 모드 전환을 위한 시각적 토글 (180x40)
- **애니메이션 드롭다운**: NDI 소스 선택 시 회전 라이트 효과
- **폰트 개선**: PVW/PGM에 Gmarket Sans Light 적용
- **레이아웃 최적화**: 드롭다운 400px 확장, CPU 표시 잘림 해결

### 📊 모니터링 정확도
- **비트레이트 계산 개선**: 프레임 데이터 기반 이동 평균 구현
- **FPS 정규화**: 59.94fps → 60fps, 60+ fps → 60fps 캡
- **CPU 모니터링 수정**: 0% 버그 해결, psutil 초기화 개선

## 상세 변경 내역

### ndi_receiver.py
```
- 프레임 페이싱 로직 완전 제거
- Non-blocking timeout 구현 (proxy: 0ms, normal: 20ms)
- _get_frame_data_size() 메서드 추가
- 이동 평균 비트레이트 계산 구현
- 오디오/메타데이터 프레임 크기 계산 포함
```

### main_window.py
```
- QDialog import 추가
- CPU 모니터링 psutil 초기화 개선
- SRT 스트림 재개 로직 수정
```

### control_panel.py
```
- ModernToggle 컴포넌트 통합
- AnimatedSourceComboBox 구현
- 버튼 텍스트 "NDI소스 재탐색" 변경
```

### modern_toggle.py (신규)
```
- 180x40 모던 토글 스위치
- 프록시 모드: 파란색 + "프록시" 라벨
- 일반 모드: 초록색 + "일반" 라벨
- QPropertyAnimation 부드러운 전환
```

### animated_button.py (신규)
```
- 회전 라이트 효과 애니메이션
- NDI 소스 미선택 시 강조 표시
```

## 해결된 이슈

1. **#001**: 모니터 끊김 현상 (프레임 페이싱 제거로 해결)
2. **#002**: 프록시 모드 40fps 제한 (Non-blocking timeout으로 해결)
3. **#003**: 비트레이트 <0.1 Mbps 표시 (프레임 데이터 기반 계산)
4. **#004**: FPS 60 초과 표시 (정규화 로직 추가)
5. **#005**: CPU 0% 표시 버그 (psutil 초기화 수정)
6. **#006**: QDialog NameError (import 추가)
7. **#007**: ToggleSwitch NameError (import 추가)

## 문서 업데이트

- PROJECT_PROGRESS_SUMMARY.md (신규)
- NDI_PROXY_MODE_OPTIMIZATION.md (업데이트)
- 비트레이트_표시_문제_해결방법.md (업데이트)
- 작업요청사항.md (완료 표시)
- BITRATE_IMPLEMENTATION_SUMMARY.md (신규)

## 성능 지표

| 항목 | 이전 | 이후 |
|------|------|------|
| 프록시 FPS | 40-43 | **60** |
| 프록시 CPU | 20-25% | **10-15%** |
| 프레임 지연 | 23-25ms | **<16ms** |
| 비트레이트 표시 | <0.1 Mbps | **정상** |

## 다음 단계

1. 네트워크 레벨 비트레이트 측정 구현
2. GPU 가속 지원 검토
3. 다중 소스 동시 모니터링 기능