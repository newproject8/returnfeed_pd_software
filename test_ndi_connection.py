#!/usr/bin/env python3
"""
NDI 연결 테스트 스크립트
"""

import sys
import os
import time

# NDI DLL 경로 추가
NDI_SDK_DLL_PATH = r"C:\Program Files\NDI\NDI 6 SDK\Bin\x64"
if sys.platform == "win32" and hasattr(os, 'add_dll_directory'):
    if os.path.isdir(NDI_SDK_DLL_PATH):
        os.add_dll_directory(NDI_SDK_DLL_PATH)
        print(f"Added to DLL search path: {NDI_SDK_DLL_PATH}")

import NDIlib as ndi

def test_ndi_connection():
    print("NDI 연결 테스트 시작...")
    
    # NDI 초기화
    if not ndi.initialize():
        print("ERROR: NDI 초기화 실패")
        return False
    
    print("NDI 초기화 성공")
    
    try:
        # NDI 소스 검색
        print("NDI 소스 검색 중...")
        find_create = ndi.FindCreate()
        ndi_find = ndi.find_create_v2(find_create)
        
        if not ndi_find:
            print("ERROR: NDI finder 생성 실패")
            return False
            
        # 소스 검색 대기
        time.sleep(2)
        
        # 소스 목록 가져오기
        sources = ndi.find_get_current_sources(ndi_find)
        
        if not sources:
            print("발견된 NDI 소스가 없습니다.")
            ndi.find_destroy(ndi_find)
            return False
            
        print(f"발견된 NDI 소스 수: {len(sources)}")
        for i, source in enumerate(sources):
            print(f"  소스 {i}: {source.ndi_name} ({source.url_address})")
            
        # 첫 번째 소스에 연결 시도
        if len(sources) > 0:
            test_source = sources[0]
            print(f"\n연결 테스트: {test_source.ndi_name}")
            
            # 수신기 생성
            recv_create = ndi.RecvCreateV3()
            recv_create.color_format = ndi.RECV_COLOR_FORMAT_BGRX_BGRA
            recv_create.bandwidth = ndi.RECV_BANDWIDTH_HIGHEST
            recv_create.allow_video_fields = False
            
            ndi_recv = ndi.recv_create_v3(recv_create)
            
            if not ndi_recv:
                print("ERROR: NDI 수신기 생성 실패")
                ndi.find_destroy(ndi_find)
                return False
                
            print("NDI 수신기 생성 성공")
            
            # 소스 연결
            ndi.recv_connect(ndi_recv, test_source)
            print("소스 연결 시도 완료")
            
            # 연결 상태 확인을 위해 잠시 대기
            time.sleep(1)
            
            # 연결 상태 확인
            print("연결 상태 확인 중...")
            time.sleep(2)  # 연결이 안정화될 때까지 대기
            
            # 프레임 수신 테스트
            print("프레임 수신 테스트 중...")
            frame_received = False
            for i in range(30):  # 더 많은 시도
                try:
                    # recv_capture_v2는 튜플을 반환합니다
                    result = ndi.recv_capture_v2(ndi_recv, 1000)  # 더 긴 타임아웃
                    frame_type, video_frame, audio_frame, metadata_frame = result
                    
                    if frame_type == ndi.FRAME_TYPE_VIDEO:
                        print(f"✅ 비디오 프레임 수신됨: {video_frame.xres}x{video_frame.yres}")
                        ndi.recv_free_video_v2(ndi_recv, video_frame)
                        frame_received = True
                        break
                    elif frame_type == ndi.FRAME_TYPE_AUDIO:
                        print(f"🔊 오디오 프레임 수신됨: {audio_frame.no_samples} samples")
                        ndi.recv_free_audio_v2(ndi_recv, audio_frame)
                        frame_received = True
                    elif frame_type == ndi.FRAME_TYPE_METADATA:
                        print(f"📄 메타데이터 프레임 수신됨: {metadata_frame.data}")
                        ndi.recv_free_metadata(ndi_recv, metadata_frame)
                    elif frame_type == ndi.FRAME_TYPE_NONE:
                        if i % 5 == 0:  # 5번마다 출력
                            print(f"⏳ 프레임 대기 중... (시도 {i+1}/30)")
                        time.sleep(0.1)
                    else:
                        print(f"❓ 알 수 없는 프레임 타입: {frame_type}")
                        
                except Exception as e:
                    print(f"❌ 프레임 캡처 중 오류: {e}")
                    break
                    
            if not frame_received:
                print("⚠️  프레임을 수신하지 못했습니다. 소스가 활성화되어 있는지 확인하세요.")
                return False
                    
            # 정리
            ndi.recv_destroy(ndi_recv)
            print("NDI 수신기 정리 완료")
            
        ndi.find_destroy(ndi_find)
        print("NDI finder 정리 완료")
        
        return True
        
    except Exception as e:
        print(f"ERROR: 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        ndi.destroy()
        print("NDI 라이브러리 정리 완료")

if __name__ == "__main__":
    success = test_ndi_connection()
    if success:
        print("\n✅ NDI 연결 테스트 성공!")
    else:
        print("\n❌ NDI 연결 테스트 실패!")