'use strict';

const { contextBridge, ipcRenderer } = require('electron');
const { randomUUID } = require('node:crypto');
const { createRendererApi } = require('./preload-api.cjs');

const rendererApi = createRendererApi({
  invoke(channel, request) {
    return ipcRenderer.invoke(channel, request);
  },
  randomUUID,
});

contextBridge.exposeInMainWorld('flowkitHost', rendererApi);
