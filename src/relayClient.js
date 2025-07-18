const WebSocket = require('ws');
const EventEmitter = require('events');

class RelayClient extends EventEmitter {
  constructor() {
    super();
    this.ws = null;
    this.isConnected = false;
    this.url = null;
    this.sessionId = null;
    this.authToken = null;
    this.reconnectTimer = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.heartbeatInterval = null;
    this.connectionId = null;
  }

  connect(url, sessionId, authToken = null) {
    return new Promise((resolve, reject) => {
      if (this.isConnected) {
        return resolve();
      }

      this.url = url;
      this.sessionId = sessionId;
      this.authToken = authToken;

      try {
        // WebSocket URL 구성
        const wsUrl = new URL(url);
        if (sessionId) {
          wsUrl.searchParams.set('sessionId', sessionId);
        }
        if (authToken) {
          wsUrl.searchParams.set('token', authToken);
        }

        console.log(`RelayClient WebSocket 연결 시도: ${wsUrl.toString()}`);
        this.ws = new WebSocket(wsUrl.toString());

        // 연결 타임아웃 설정
        const connectTimeout = setTimeout(() => {
          if (this.ws) {
            this.ws.close();
          }
          reject(new Error('릴레이 서버 연결 시간 초과'));
        }, 10000);

        this.ws.on('open', () => {
          clearTimeout(connectTimeout);
          this.isConnected = true;
          this.reconnectAttempts = 0;
          console.log('RelayClient WebSocket 연결 완료');

          // PD 역할로 등록
          this.register();
          
          // 하트비트 시작
          this.startHeartbeat();
          
          this.emit('connected');
          resolve();
        });

        this.ws.on('message', (data) => {
          try {
            const message = JSON.parse(data.toString());
            this.handleMessage(message);
          } catch (error) {
            console.error('RelayClient 메시지 파싱 오류:', error);
          }
        });

        this.ws.on('close', (code, reason) => {
          console.log(`RelayClient WebSocket 연결 종료: ${code} - ${reason}`);
          this.handleDisconnection();
        });

        this.ws.on('error', (error) => {
          console.error('RelayClient WebSocket 오류:', error);
          clearTimeout(connectTimeout);
          this.emit('error', error);
          
          if (!this.isConnected) {
            reject(error);
          }
        });

      } catch (error) {
        console.error('RelayClient 연결 설정 오류:', error);
        reject(error);
      }
    });
  }

  disconnect() {
    this.reconnectAttempts = this.maxReconnectAttempts; // 재연결 방지
    this.stopHeartbeat();
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.isConnected = false;
    console.log('RelayClient 연결 해제됨');
  }

  register() {
    if (!this.isConnected || !this.ws) return;

    const registerMessage = {
      type: 'register',
      sessionId: this.sessionId,
      role: 'pd',
      timestamp: new Date().toISOString()
    };

    this.sendMessage(registerMessage);
    console.log('RelayClient PD 역할로 등록 요청');
  }

  sendTallyData(tallyData) {
    if (!this.isConnected || !this.ws) {
      console.warn('RelayClient: 연결되지 않음 - Tally 데이터 전송 실패');
      return false;
    }

    try {
      const message = {
        type: 'tally_update',
        sessionId: this.sessionId,
        program: tallyData.program,
        preview: tallyData.preview,
        inputs: tallyData.inputs || {},
        timestamp: new Date().toISOString(),
        vmixTimestamp: tallyData.timestamp
      };

      this.sendMessage(message);
      console.log(`RelayClient: Tally 데이터 전송 - Program: ${tallyData.program}, Preview: ${tallyData.preview}`);
      return true;
    } catch (error) {
      console.error('RelayClient: Tally 데이터 전송 오류:', error);
      this.emit('error', error);
      return false;
    }
  }

  sendInputsData(inputsData) {
    if (!this.isConnected || !this.ws) {
      console.warn('RelayClient: 연결되지 않음 - Inputs 데이터 전송 실패');
      return false;
    }

    try {
      const message = {
        type: 'inputs_update',
        sessionId: this.sessionId,
        inputs: inputsData.inputs || {},
        vmixVersion: inputsData.version || 'unknown',
        timestamp: new Date().toISOString(),
        vmixTimestamp: inputsData.timestamp
      };

      this.sendMessage(message);
      console.log(`RelayClient: Inputs 데이터 전송 - ${Object.keys(inputsData.inputs || {}).length}개 카메라`);
      return true;
    } catch (error) {
      console.error('RelayClient: Inputs 데이터 전송 오류:', error);
      this.emit('error', error);
      return false;
    }
  }

  sendMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('RelayClient: WebSocket 연결이 열려있지 않음');
    }
  }

  handleMessage(message) {
    console.log('RelayClient 메시지 수신:', message.type);

    switch (message.type) {
      case 'connected':
        this.connectionId = message.clientId;
        console.log(`RelayClient: 서버 연결 확인 (ID: ${this.connectionId})`);
        break;

      case 'session_registered':
        console.log(`RelayClient: 세션 등록 완료 - ${message.sessionId}`);
        this.emit('session_registered', message);
        break;

      case 'pong':
        // 하트비트 응답
        break;

      case 'error':
        console.error('RelayClient 서버 오류:', message.message);
        this.emit('error', new Error(message.message));
        break;

      default:
        console.log(`RelayClient: 알 수 없는 메시지 타입: ${message.type}`);
    }
  }

  handleDisconnection() {
    this.isConnected = false;
    this.stopHeartbeat();
    this.emit('disconnected');
    
    // 자동 재연결
    if (this.reconnectAttempts < this.maxReconnectAttempts && this.url) {
      this.scheduleReconnect();
    } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('RelayClient: 최대 재연결 시도 횟수 초과');
      this.emit('max_reconnect_reached');
    }
  }

  scheduleReconnect() {
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
    console.log(`RelayClient: ${delay}ms 후 재연결 시도... (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
    
    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect(this.url, this.sessionId, this.authToken)
        .catch((error) => {
          console.error(`RelayClient 재연결 실패 (${this.reconnectAttempts}/${this.maxReconnectAttempts}):`, error.message);
        });
    }, delay);
  }

  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected && this.ws) {
        this.sendMessage({
          type: 'ping',
          timestamp: new Date().toISOString()
        });
      }
    }, 30000); // 30초마다 ping
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  // main.js에서 사용하는 메서드들
  isConnected() {
    return this.isConnected;
  }

  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      url: this.url,
      sessionId: this.sessionId,
      connectionId: this.connectionId,
      reconnectAttempts: this.reconnectAttempts
    };
  }

  // 세션 정보 업데이트
  updateSession(sessionId, authToken = null) {
    this.sessionId = sessionId;
    this.authToken = authToken;
    
    if (this.isConnected) {
      this.register(); // 새 세션으로 재등록
    }
  }

  // 서버 연결 테스트
  async testConnection() {
    try {
      if (this.isConnected && this.ws) {
        this.sendMessage({
          type: 'ping',
          timestamp: new Date().toISOString()
        });
        return true;
      }
      return false;
    } catch (error) {
      console.error('RelayClient 연결 테스트 실패:', error);
      return false;
    }
  }
}

module.exports = RelayClient;