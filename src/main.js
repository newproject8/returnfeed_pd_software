const { app, BrowserWindow, ipcMain, Menu, Tray, dialog } = require('electron');
const path = require('path');
const Store = require('electron-store');
const VmixClient = require('./vmixClient');
const RelayClient = require('./relayClient');

// 설정 저장소
const store = new Store();

// 전역 변수
let mainWindow = null;
let tray = null;
let vmixClient = null;
let relayClient = null;
let isConnected = false;

// 개발 모드 확인
const isDev = process.argv.includes('--dev');

// 창 생성
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 600,
    height: 800,
    minWidth: 500,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '../assets/icon.png'),
    title: 'ReturnFeed PD Software'
  });

  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // 창이 최소화될 때 트레이로
  mainWindow.on('minimize', (event) => {
    if (!isDev) {
      event.preventDefault();
      mainWindow.hide();
    }
  });
}

// 트레이 아이콘 생성
function createTray() {
  tray = new Tray(path.join(__dirname, '../assets/tray.png'));
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: '열기',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
        }
      }
    },
    {
      label: '연결 상태',
      sublabel: isConnected ? '연결됨' : '연결 안됨',
      enabled: false
    },
    { type: 'separator' },
    {
      label: '종료',
      click: () => {
        app.quit();
      }
    }
  ]);

  tray.setToolTip('ReturnFeed PD Software');
  tray.setContextMenu(contextMenu);

  tray.on('click', () => {
    if (mainWindow) {
      mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
    }
  });
}

// 앱 초기화
app.whenReady().then(() => {
  createWindow();
  createTray();

  // 클라이언트 초기화
  vmixClient = new VmixClient();
  relayClient = new RelayClient();

  // 저장된 설정 불러오기
  const savedSettings = store.get('settings', {
    vmixHost: '127.0.0.1',
    vmixPort: 8099,
    relayUrl: 'wss://returnfeed.net/ws/',
    sessionId: '',
    autoConnect: false
  });

  // 설정을 렌더러로 전송
  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow.webContents.send('settings-loaded', savedSettings);
  });
});

// 앱 종료 시
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// IPC 핸들러

// 설정 저장
ipcMain.handle('save-settings', async (event, settings) => {
  store.set('settings', settings);
  return { success: true };
});

// vMix 연결
ipcMain.handle('connect-vmix', async (event, { host, port }) => {
  try {
    await vmixClient.connect(host, port);
    
    // Tally 업데이트 리스너
    vmixClient.on('tally-update', (tallyData) => {
      mainWindow.webContents.send('tally-data', tallyData);
      
      // Relay 서버로 전송
      if (relayClient.isConnected()) {
        relayClient.sendTallyData(tallyData);
      }
    });

    // Inputs 업데이트 리스너 (카메라 목록 변경)
    vmixClient.on('inputs-update', (inputsData) => {
      mainWindow.webContents.send('inputs-data', inputsData);
      
      // Relay 서버로 전송
      if (relayClient.isConnected()) {
        relayClient.sendInputsData(inputsData);
      }
    });

    vmixClient.on('error', (error) => {
      mainWindow.webContents.send('vmix-error', error.message);
    });

    vmixClient.on('disconnected', () => {
      mainWindow.webContents.send('vmix-disconnected');
      isConnected = false;
      updateTrayStatus();
    });

    isConnected = true;
    updateTrayStatus();
    
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// vMix 연결 해제
ipcMain.handle('disconnect-vmix', async () => {
  vmixClient.disconnect();
  isConnected = false;
  updateTrayStatus();
  return { success: true };
});

// Relay 서버 연결
ipcMain.handle('connect-relay', async (event, { url, sessionId }) => {
  try {
    await relayClient.connect(url, sessionId);
    
    relayClient.on('connected', () => {
      mainWindow.webContents.send('relay-connected');
    });

    relayClient.on('error', (error) => {
      mainWindow.webContents.send('relay-error', error.message);
    });

    relayClient.on('disconnected', () => {
      mainWindow.webContents.send('relay-disconnected');
    });

    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Relay 서버 연결 해제
ipcMain.handle('disconnect-relay', async () => {
  relayClient.disconnect();
  return { success: true };
});

// 트레이 상태 업데이트
function updateTrayStatus() {
  if (!tray) return;
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: '열기',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
        }
      }
    },
    {
      label: '연결 상태',
      sublabel: isConnected ? '연결됨' : '연결 안됨',
      enabled: false
    },
    { type: 'separator' },
    {
      label: '종료',
      click: () => {
        app.quit();
      }
    }
  ]);

  tray.setContextMenu(contextMenu);
}

// 로그 전송
ipcMain.on('log', (event, message) => {
  console.log('[Renderer]:', message);
});