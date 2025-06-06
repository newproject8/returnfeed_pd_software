import socket
import sys

# --- 여기에 테스트할 서버의 도메인과 포트를 입력하세요 ---
SERVER_ADDRESS = "203.234.214.201"
SERVER_PORT = 4431
# ----------------------------------------------------

def check_port(address, port):
    """지정된 주소와 포트로 TCP 소켓 연결을 시도합니다."""
    print(f"'{address}:{port}' 주소로 연결을 시도합니다...")
    
    # 소켓 생성
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 연결 시도 시간 제한 (3초)
        sock.settimeout(3)
        
        # 연결 시도
        result = sock.connect_ex((address, port))
        
        if result == 0:
            print("-----------------------------------------")
            print("✅ 성공! 포트가 열려있고, 서버에 연결할 수 있습니다.")
            print("-----------------------------------------")
            print("이제 PD용 앱이 정상적으로 작동해야 합니다.")
        else:
            print("----------------------------------------------------------")
            print(f"❌ 실패! 포트가 닫혀 있거나, 서버에 도달할 수 없습니다.")
            print("----------------------------------------------------------")
            print("원인:")
            print("1. 인터넷 통신사(KT, SKT 등)가 이 포트를 차단했을 수 있습니다.")
            print("2. 공유기 포트포워딩 설정이 잘못되었을 수 있습니다. (다시 확인 필요)")
            print("3. 헤놀로지 NAS의 다른 네트워크 설정 문제일 수 있습니다.")
            
    except socket.gaierror:
        print("----------------------------------------------------------")
        print(f"❌ 실패! '{address}' 라는 주소(도메인)를 찾을 수 없습니다.")
        print("----------------------------------------------------------")
        print("원인:")
        print("1. 도메인 이름에 오타가 없는지 확인하세요.")
        print("2. 도메인과 IP 주소가 올바르게 연결되었는지 다시 확인하세요.")
        
    except Exception as e:
        print(f"알 수 없는 오류가 발생했습니다: {e}")
        
    finally:
        sock.close()
        input("\n엔터 키를 누르면 종료됩니다...")


if __name__ == "__main__":
    check_port(SERVER_ADDRESS, SERVER_PORT)

