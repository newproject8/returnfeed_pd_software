import socket

HOST = 'www.returnfeed.net' # 서버 도메인
PORT = 8765             # 서버 포트

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    print(f"{HOST}:{PORT} 에 연결을 시도합니다...")
    try:
        s.connect((HOST, PORT))
        print("✅ 서버에 성공적으로 연결되었습니다!")

        # 서버에 메시지 보내기
        message = "안녕하세요, 테스트 메시지입니다."
        print(f" > 전송: {message}")
        s.sendall(message.encode('utf-8'))

        # 서버로부터 에코(메아리) 메시지 받기
        data = s.recv(1024)
        print(f" < 수신: {data.decode('utf-8')}")

        if data.decode('utf-8') == message:
            print("\n🎉 테스트 성공! 데이터가 성공적으로 오고 갔습니다.")
        else:
            print("\n❌ 테스트 실패! 데이터가 일치하지 않습니다.")

    except Exception as e:
        print(f"\n❌ 연결 실패: {e}")

    finally:
        input("\n엔터 키를 누르면 종료됩니다...")