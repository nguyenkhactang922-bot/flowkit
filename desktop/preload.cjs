'use strict';

// Electron sandboxed preloads cannot require arbitrary local CommonJS modules.
// Keep this boundary self-contained; ipc-main.cjs remains the canonical deep
// request/response validator before any result crosses back to the Renderer.
const { contextBridge, ipcRenderer } = require('electron');

const IPC_PROTOCOL_VERSION = 1;
const CHANNELS = Object.freeze({
  GET_BRIDGE_STATUS: 'flowkit:utility:get-bridge-status',
  GET_STUDIO_APPLICATION_READ_MODEL: 'flowkit:studio:get-application-read-model',
});
let requestSequence = 0;

function createRequestId() {
  const webCrypto = globalThis.crypto;
  if (webCrypto && typeof webCrypto.randomUUID === 'function') {
    return webCrypto.randomUUID();
  }
  requestSequence += 1;
  return 'req-' + Date.now().toString(36) + '-' + requestSequence.toString(36);
}

function validateResponseEnvelope(response, requestId) {
  if (
    response === null ||
    typeof response !== 'object' ||
    Array.isArray(response) ||
    Object.keys(response).sort().join('|') !== 'apiVersion|data|error|ok|requestId' ||
    response.apiVersion !== IPC_PROTOCOL_VERSION ||
    response.requestId !== requestId ||
    typeof response.ok !== 'boolean'
  ) {
    throw new Error('Invalid IPC response.');
  }

  if (response.ok) {
    if (response.error !== null || response.data === null) {
      throw new Error('Invalid IPC response.');
    }
  } else if (
    response.data !== null ||
    response.error === null ||
    typeof response.error !== 'object' ||
    Object.keys(response.error).sort().join('|') !== 'code|message' ||
    typeof response.error.code !== 'string' ||
    response.error.message !== 'Request could not be completed.'
  ) {
    throw new Error('Invalid IPC response.');
  }
  return response;
}

const productionUtility = Object.freeze({
  async getBridgeStatus() {
    const requestId = createRequestId();
    const response = await ipcRenderer.invoke(CHANNELS.GET_BRIDGE_STATUS, {
      apiVersion: IPC_PROTOCOL_VERSION,
      requestId,
    });
    return validateResponseEnvelope(response, requestId);
  },
});

const studio = Object.freeze({
  async getApplicationReadModel(projectId) {
    const requestId = createRequestId();
    const response = await ipcRenderer.invoke(CHANNELS.GET_STUDIO_APPLICATION_READ_MODEL, {
      apiVersion: IPC_PROTOCOL_VERSION,
      requestId,
      projectId,
    });
    return validateResponseEnvelope(response, requestId);
  },
});

const rendererApi = Object.freeze({
  apiVersion: IPC_PROTOCOL_VERSION,
  securityBaseline: 'imp-070-v1',
  ipcBaseline: 'imp-071-v1',
  productionUtility,
  studio,
});

contextBridge.exposeInMainWorld('flowkitHost', rendererApi);
