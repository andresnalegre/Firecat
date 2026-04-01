const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('firecat', {
  version:  '1.0.0',
  platform: process.platform,

  onDownloadProgress: (callback) => {
    ipcRenderer.on('download-progress', (event, data) => callback(data))
  },

  removeDownloadListeners: () => {
    ipcRenderer.removeAllListeners('download-progress')
  },

  openDownloads: () => {
    ipcRenderer.send('open-downloads')
  },

  clearCache: () => {
    return ipcRenderer.invoke('clear-cache')
  },

  openDevTools: () => {
    ipcRenderer.send('open-devtools')
  },

  isFullscreen: () => {
    return ipcRenderer.sendSync('is-fullscreen')
  },

  onFullscreenChange: (callback) => {
    ipcRenderer.on('fullscreen-change', (event, val) => callback(val))
  },
})