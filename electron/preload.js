const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('firecat', {
  version:  '1.0.0',
  platform: process.platform,

  onDownloadProgress: (callback) => {
    const handler = (event, data) => callback(data)
    ipcRenderer.on('download-progress', handler)
    return () => ipcRenderer.removeListener('download-progress', handler)
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
    const handler = (event, val) => callback(val)
    ipcRenderer.on('fullscreen-change', handler)
    return () => ipcRenderer.removeListener('fullscreen-change', handler)
  },
})