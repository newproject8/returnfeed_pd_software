# NDI 프레임레이트 문제 해결 보고서

## 문제 분석
- **증상**: NDI 일반/프록시 모드에서 화면이 뚝뚝 끊김
- **원인**: CPU 스피닝으로 인한 리소스 경합

## 적용된 해결책

### 1. 스레드 우선순위 설정
```python
# Windows에서 실시간 비디오 처리를 위한 높은 우선순위
kernel32.SetThreadPriority(handle, 2)  # THREAD_PRIORITY_HIGHEST
```

### 2. 블로킹 타임아웃 증가
```python
# 기존: timeout_ms = 20 (CPU 스피닝 유발)
# 변경: timeout_ms = 100 (CPU 양보, 다른 스레드 실행 가능)
```

### 3. 프레임 포맷 최적화
- NDIlib_recv_color_format_BGRX_BGRA 사용 (이미 적용됨)
- CPU 변환 없이 GPU에서 직접 처리 가능

### 4. 메모리 복사 최적화
- 프록시 모드: ascontiguousarray 사용으로 불필요한 복사 최소화
- 일반 모드: 안전한 깊은 복사 유지

## 추가 권장사항

### 단기 해결책
1. NDI Analysis Tool로 네트워크 상태 진단
   ```bash
   NDIAnalysis.exe /source:"NEWPROJECT (vMix - Output 1)" /bandwidth:lowest /csvvideo:"proxy_analysis.csv"
   ```

2. 디지터 버퍼 구현 검토 (네트워크 지터가 심한 경우)

### 장기 해결책
1. **GPU 가속 렌더링 도입** (QOpenGLWidget 기반)
   - CPU 렌더링 병목 완전 해소
   - NDI 공식 권장 아키텍처

2. **별도 렌더링 스레드 구현**
   - 수신 스레드와 렌더링 스레드 분리
   - 생산자-소비자 패턴 적용

## 테스트 방법
1. 일반 모드 테스트
2. 프록시 모드 테스트
3. CPU 사용률 모니터링
4. 프레임레이트 확인

## 참고
- NDI 공식 백서: https://docs.ndi.video/all/getting-started/white-paper
- 문서 기반 최적화 적용 완료