const net = require('net');
const xml2js = require('xml2js');
const EventEmitter = require('events');
const http = require('http');

class VmixClient extends EventEmitter {
  constructor() {
    super();
    this.client = null;
    this.isConnected = false;
    this.buffer = '';
    this.parser = new xml2js.Parser({ explicitArray: false });
    this.reconnectTimer = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.tallyInterval = null;
    this.inputsInterval = null;
    this.vmixHost = null;
    this.vmixTcpPort = null;
    this.vmixHttpPort = 8088; // vMix HTTP API 기본 포트
    this.lastInputsData = null;
    this.isSubscribedToTally = false;
  }

  connect(host, port) {
    return new Promise((resolve, reject) => {
      if (this.isConnected) {
        return resolve();
      }

      this.vmixHost = host;
      this.vmixTcpPort = port;
      this.client = new net.Socket();
      
      // 연결 타임아웃 설정
      const connectTimeout = setTimeout(() => {
        this.client.destroy();
        reject(new Error('vMix 연결 시간 초과'));
      }, 10000);

      this.client.connect(port, host, () => {
        clearTimeout(connectTimeout);
        this.isConnected = true;
        this.reconnectAttempts = 0;
        console.log(`vMix TCP 연결됨: ${host}:${port}`);
        
        // vMix API 문서에 따른 초기 설정
        this.subscribeTally();
        this.requestFullXML();
        this.startPolling();
        
        resolve();
      });

      this.client.on('data', (data) => {
        this.handleData(data);
      });

      this.client.on('close', () => {
        this.isConnected = false;
        this.stopPolling();
        this.emit('disconnected');
        
        // 자동 재연결
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect(host, port);
        }
      });

      this.client.on('error', (err) => {
        console.error('vMix 연결 오류:', err);
        clearTimeout(connectTimeout);
        this.emit('error', err);
        
        if (!this.isConnected) {
          reject(err);
        }
      });
    });
  }

  disconnect() {
    this.reconnectAttempts = this.maxReconnectAttempts; // 재연결 방지
    this.stopPolling();
    
    // TALLY 구독 해제
    this.unsubscribeTally();
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.client) {
      this.client.destroy();
      this.client = null;
    }
    
    this.isConnected = false;
    this.isSubscribedToTally = false;
    this.lastInputsData = null;
    console.log('vMix 클라이언트 연결 해제됨');
  }

  handleData(data) {
    const dataStr = data.toString();
    this.buffer += dataStr;
    
    // TALLY 응답 처리 (간단한 문자열)
    if (this.buffer.includes('\r\n') && !this.buffer.includes('<')) {
      const lines = this.buffer.split('\r\n');
      for (let i = 0; i < lines.length - 1; i++) {
        const line = lines[i].trim();
        if (line.length > 0 && /^[012]+$/.test(line)) {
          // TALLY 응답 처리
          this.parseTallyResponse(line);
        }
      }
      this.buffer = lines[lines.length - 1];
    }
    
    // XML 응답 처리
    if (this.buffer.includes('</vmix>')) {
      const xmlEnd = this.buffer.indexOf('</vmix>') + 7;
      const xmlString = this.buffer.substring(0, xmlEnd);
      this.buffer = this.buffer.substring(xmlEnd);
      
      this.parseXML(xmlString);
    }
  }

  async parseXML(xmlString) {
    try {
      const result = await this.parser.parseStringPromise(xmlString);
      
      if (result.vmix) {
        // Inputs 정보 추출 및 전송
        if (result.vmix.inputs && result.vmix.inputs.input) {
          const inputsData = this.extractInputsData(result.vmix);
          
          // 입력 리스트가 변경되었을 때만 전송
          if (JSON.stringify(inputsData.inputs) !== JSON.stringify(this.lastInputsData)) {
            this.lastInputsData = inputsData.inputs;
            this.emit('inputs-update', inputsData);
          }
        }
        
        // Tally 정보 추출 및 전송
        const tallyData = this.extractTallyData(result.vmix);
        this.emit('tally-update', tallyData);
      }
    } catch (error) {
      console.error('XML 파싱 오류:', error);
      this.emit('error', new Error('vMix 데이터 파싱 실패'));
    }
  }

  // vMix API 문서에 따른 TALLY 응답 파싱
  parseTallyResponse(tallyString) {
    const tallyData = {
      program: null,
      preview: null,
      inputs: this.lastInputsData || {},
      timestamp: Date.now(),
      rawTally: tallyString
    };

    // TALLY 문자열: 0=off, 1=program, 2=preview
    for (let i = 0; i < tallyString.length; i++) {
      const inputNumber = i + 1;
      const state = parseInt(tallyString[i]);
      
      if (state === 1) {
        tallyData.program = inputNumber;
      } else if (state === 2) {
        tallyData.preview = inputNumber;
      }
    }

    this.emit('tally-update', tallyData);
  }

  // 입력 정보 추출 (vMix XML 구조 기반)
  extractInputsData(vmixData) {
    const inputs = Array.isArray(vmixData.inputs.input) 
      ? vmixData.inputs.input 
      : [vmixData.inputs.input];
    
    const inputsData = {
      inputs: {},
      timestamp: Date.now(),
      version: vmixData.$.version || 'unknown'
    };

    inputs.forEach((input) => {
      const number = parseInt(input.$.number);
      const title = input.$.title || `Input ${number}`;
      const type = input.$.type || 'Unknown';
      const state = input.$.state || 'Paused';
      const duration = input.$.duration || '0';
      
      inputsData.inputs[number] = {
        number,
        title,
        type,
        state,
        duration,
        shortTitle: input.$.shortTitle || title.substring(0, 10)
      };
    });

    return inputsData;
  }

  extractTallyData(vmixData) {
    const tallyData = {
      program: null,
      preview: null,
      inputs: this.lastInputsData || {},
      timestamp: Date.now()
    };

    // vMix XML 구조에서 활성 상태 확인 (공식 API 문서 기반)
    if (vmixData.active) {
      tallyData.program = parseInt(vmixData.active);
    }
    
    if (vmixData.preview) {
      tallyData.preview = parseInt(vmixData.preview);
    }

    // inputs가 있는 경우 상태 확인
    if (vmixData.inputs && vmixData.inputs.input) {
      const inputs = Array.isArray(vmixData.inputs.input) 
        ? vmixData.inputs.input 
        : [vmixData.inputs.input];
      
      inputs.forEach((input) => {
        const number = parseInt(input.$.number);
        const state = input.$.state || '';
        
        // vMix에서 Running 상태는 Program을 의미
        if (state === 'Running') {
          tallyData.program = number;
        }
        // Preview 상태는 명시적으로 preview 속성에서 확인
        if (input.$.preview === 'True') {
          tallyData.preview = number;
        }
      });
    }

    return tallyData;
  }

  // vMix API 명령어들 (공식 문서 기반)
  subscribeTally() {
    if (this.isConnected && this.client && !this.isSubscribedToTally) {
      console.log('vMix TALLY 구독 시작');
      this.client.write('SUBSCRIBE TALLY\r\n');
      this.isSubscribedToTally = true;
    }
  }

  unsubscribeTally() {
    if (this.isConnected && this.client && this.isSubscribedToTally) {
      console.log('vMix TALLY 구독 해제');
      this.client.write('UNSUBSCRIBE TALLY\r\n');
      this.isSubscribedToTally = false;
    }
  }

  requestTally() {
    if (this.isConnected && this.client) {
      this.client.write('TALLY\r\n');
    }
  }

  requestFullXML() {
    if (this.isConnected && this.client) {
      console.log('vMix 전체 XML 상태 요청');
      this.client.write('XML\r\n');
    }
  }

  // HTTP API를 통한 inputs 정보 가져오기 (백업용)
  async requestInputsViaHTTP() {
    if (!this.vmixHost) return null;

    return new Promise((resolve, reject) => {
      const options = {
        hostname: this.vmixHost,
        port: this.vmixHttpPort,
        path: '/api/?Function=XML',
        method: 'GET',
        timeout: 5000
      };

      const req = http.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => {
          data += chunk;
        });
        res.on('end', async () => {
          try {
            const result = await this.parser.parseStringPromise(data);
            if (result.vmix && result.vmix.inputs) {
              const inputsData = this.extractInputsData(result.vmix);
              resolve(inputsData);
            } else {
              resolve(null);
            }
          } catch (error) {
            reject(error);
          }
        });
      });

      req.on('error', (error) => {
        console.warn('vMix HTTP API 요청 실패:', error.message);
        reject(error);
      });

      req.on('timeout', () => {
        req.destroy();
        reject(new Error('HTTP API 요청 시간 초과'));
      });

      req.end();
    });
  }

  startPolling() {
    // vMix API 문서에 따른 최적화된 폴링
    
    // TALLY 구독을 사용하므로 별도 폴링 불필요
    // 대신 5초마다 inputs 정보 갱신
    this.inputsInterval = setInterval(() => {
      this.requestFullXML();
    }, 5000);

    // 백업용: HTTP API로 30초마다 inputs 정보 확인
    this.httpBackupInterval = setInterval(async () => {
      try {
        const inputsData = await this.requestInputsViaHTTP();
        if (inputsData && JSON.stringify(inputsData.inputs) !== JSON.stringify(this.lastInputsData)) {
          this.lastInputsData = inputsData.inputs;
          this.emit('inputs-update', inputsData);
        }
      } catch (error) {
        console.warn('HTTP 백업 요청 실패:', error.message);
      }
    }, 30000);
  }

  stopPolling() {
    if (this.tallyInterval) {
      clearInterval(this.tallyInterval);
      this.tallyInterval = null;
    }
    
    if (this.inputsInterval) {
      clearInterval(this.inputsInterval);
      this.inputsInterval = null;
    }
    
    if (this.httpBackupInterval) {
      clearInterval(this.httpBackupInterval);
      this.httpBackupInterval = null;
    }
  }

  // 연결 상태 확인용 메서드 수정
  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      isSubscribedToTally: this.isSubscribedToTally,
      host: this.vmixHost,
      tcpPort: this.vmixTcpPort,
      httpPort: this.vmixHttpPort,
      reconnectAttempts: this.reconnectAttempts
    };
  }

  scheduleReconnect(host, port) {
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
    console.log(`${delay}ms 후 vMix 재연결 시도... (시도 ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
    
    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect(host, port).catch((error) => {
        console.error(`재연결 실패 (${this.reconnectAttempts}/${this.maxReconnectAttempts}):`, error.message);
      });
    }, delay);
  }

  // 연결 상태 확인 메서드 (이름 변경으로 충돌 방지)
  checkConnectionStatus() {
    return this.isConnected;
  }
}

module.exports = VmixClient;