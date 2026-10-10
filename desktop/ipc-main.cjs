'use strict';

const {
  CHANNELS,
  IPC_ERROR_CODES,
  assertTrustedRendererSender,
  contractErrorCode,
  createRedactedErrorResponse,
  safeRequestIdFromUnknown,
  validateBridgeStatusRequest,
  validateBridgeStatusResponse,
} = require('./ipc-contract.cjs');

function installProductionIpcHandlers({ ipcMain, webContents, appOrigin, bridge }) {
  if (!ipcMain || typeof ipcMain.handle !== 'function' || typeof ipcMain.removeHandler !== 'function') {
    throw new TypeError('ipcMain handle/removeHandler are required');
  }
  if (!webContents) {
    throw new TypeError('webContents is required');
  }
  if (typeof appOrigin !== 'string' || !appOrigin.trim()) {
    throw new TypeError('appOrigin is required');
  }
  if (!bridge || typeof bridge.getBridgeStatus !== 'function') {
    throw new TypeError('ProductionUtilityBridge is required');
  }

  const channel = CHANNELS.GET_BRIDGE_STATUS;
  ipcMain.handle(channel, async (event, rawRequest) => {
    const requestId = safeRequestIdFromUnknown(rawRequest);
    try {
      assertTrustedRendererSender(event, webContents, appOrigin);
      const request = validateBridgeStatusRequest(rawRequest);
      const response = await bridge.getBridgeStatus(request);
      return validateBridgeStatusResponse(response);
    } catch (error) {
      return createRedactedErrorResponse(
        requestId,
        contractErrorCode(error, IPC_ERROR_CODES.UTILITY_UNAVAILABLE)
      );
    }
  });

  return Object.freeze({
    channels: Object.freeze([channel]),
    dispose() {
      ipcMain.removeHandler(channel);
    },
  });
}

module.exports = { installProductionIpcHandlers };
