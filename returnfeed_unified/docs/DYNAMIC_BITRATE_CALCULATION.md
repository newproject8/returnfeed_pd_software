# 동적 비트레이트 계산 구현

최종 업데이트: 2025-07-16

## 개요
고정된 표준값이 아닌, 실제 해상도와 압축률을 고려한 동적 비트레이트 계산 구현

## 계산 방식

### 1. Raw 데이터 크기 계산
```python
raw_bps = width * height * 4 * 8 * fps  # 4 bytes/pixel, 8 bits/byte
raw_mbps = raw_bps / 1_000_000
```

### 2. 압축률 적용
실제 NDI 문서 기반으로 압축률을 역산하여 적용

## 주요 비트레이트 목표값

### 일반 모드 (SpeedHQ)
- **1920x1080 60fps**: 165.17 Mbps (사용자 지정 최대값)
- **1280x720 60fps**: 105.83 Mbps (NDI 문서 기준)
- **3840x2160 60fps**: 249.99 Mbps (NDI 문서 기준)

### 프록시 모드 (H.264/H.265 수준)
- **640x360 60fps**: 30 Mbps (사용자 지정 최대값)
- **1920x1080 60fps**: 120 Mbps (사용자 지정 최대값)

## 압축률 계산 예시

### FHD 60fps 일반 모드
```
Raw: 1920 × 1080 × 4 × 8 × 60 = 1,990,656,000 bps = 1990.7 Mbps
목표: 165.17 Mbps
압축률: 165.17 / 1990.7 = 8.29%
```

### 640x360 60fps 프록시 모드
```
Raw: 640 × 360 × 4 × 8 × 60 = 442,368,000 bps = 442.4 Mbps
목표: 30 Mbps
압축률: 30 / 442.4 = 6.78%
```

## 구현 특징

1. **정확한 값 우선**: 특정 해상도에 대해 NDI 문서의 정확한 값 사용
2. **동적 계산**: 문서에 없는 해상도는 근사 압축률 적용
3. **모드별 차별화**: 일반 모드는 SpeedHQ, 프록시 모드는 H.264/H.265 수준
4. **로깅**: 첫 계산 시 raw 및 압축된 비트레이트와 압축률 표시

## 장점
- 해상도에 관계없이 합리적인 비트레이트 표시
- NDI 문서 기반의 정확한 계산
- 사용자 요구사항 반영 (FHD 165.17 Mbps, 프록시 30/120 Mbps)
- 투명한 계산 과정 (로그 출력)

## 참고 자료
- `/docs/ndi_bitrate_table.md` - NDI 공식 비트레이트 테이블
- NDI SDK 문서 - SpeedHQ 코덱 사양