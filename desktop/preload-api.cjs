'use strict';

const {
  CHANNELS,
  IPC_PROTOCOL_VERSION,
  validateBridgeStatusResponse,
  validateStudioApplicationReadModelResponse,
} = require('./ipc-contract.cjs');

function createRendererApi({ invoke, randomUUID }) {
  if (typeof invoke !== 'function') {
    throw new TypeError('invoke function is required');
  }
  if (typeof randomUUID !== 'function') {
    throw new TypeError('randomUUID function is required');
  }

  const productionUtility = Object.freeze({
    async getBridgeStatus() {
      const response = await invoke(CHANNELS.GET_BRIDGE_STATUS, {
        apiVersion: IPC_PROTOCOL_VERSION,
        requestId: randomUUID(),
      });
      return validateBridgeStatusResponse(response);
    },
  });

  const studio = Object.freeze({
    async getApplicationReadModel(projectId) {
      const response = await invoke(CHANNELS.GET_STUDIO_APPLICATION_READ_MODEL, {
        apiVersion: IPC_PROTOCOL_VERSION,
        requestId: randomUUID(),
        projectId,
      });
      return validateStudioApplicationReadModelResponse(response, projectId);
    },
  });

  return Object.freeze({
    apiVersion: IPC_PROTOCOL_VERSION,
    securityBaseline: 'imp-070-v1',
    ipcBaseline: 'imp-071-v1',
    productionUtility,
    studio,
  });
}

module.exports = { createRendererApi };
