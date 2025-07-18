const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Settings
  saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),
  onSettingsLoaded: (callback) => ipcRenderer.on('settings-loaded', callback),

  // vMix Connection
  connectVmix: (config) => ipcRenderer.invoke('connect-vmix', config),
  disconnectVmix: () => ipcRenderer.invoke('disconnect-vmix'),
  
  // Relay Connection
  connectRelay: (config) => ipcRenderer.invoke('connect-relay', config),
  disconnectRelay: () => ipcRenderer.invoke('disconnect-relay'),

  // Event Listeners
  onTallyData: (callback) => ipcRenderer.on('tally-data', callback),
  onInputsData: (callback) => ipcRenderer.on('inputs-data', callback),
  onVmixError: (callback) => ipcRenderer.on('vmix-error', callback),
  onVmixDisconnected: (callback) => ipcRenderer.on('vmix-disconnected', callback),
  onRelayConnected: (callback) => ipcRenderer.on('relay-connected', callback),
  onRelayError: (callback) => ipcRenderer.on('relay-error', callback),
  onRelayDisconnected: (callback) => ipcRenderer.on('relay-disconnected', callback),

  // Logging
  log: (message) => ipcRenderer.send('log', message),

  // Remove listeners
  removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel)
});