const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('jarvisNative', {
  getConfig: () => ipcRenderer.invoke('jarvis:get-config')
});
