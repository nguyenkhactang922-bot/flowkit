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
  validateStudioApplicationReadModelRequest,
  validateStudioApplicationReadModelResponse,
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
  if (
    !bridge ||
    typeof bridge.getBridgeStatus !== 'function' ||
    typeof bridge.getApplicationReadModel !== 'function'
  ) {
    throw new TypeError('ProductionUtilityBridge is required');
  }

  const registrations = [
    {
      channel: CHANNELS.GET_BRIDGE_STATUS,
      validateRequest: validateBridgeStatusRequest,
      invoke: (request) => bridge.getBridgeStatus(request),
      validateResponse: validateBridgeStatusResponse,
    },
    {
      channel: CHANNELS.GET_STUDIO_APPLICATION_READ_MODEL,
      validateRequest: validateStudioApplicationReadModelRequest,
      invoke: (request) => bridge.getApplicationReadModel(request),
      validateResponse: (response, request) =>
        validateStudioApplicationReadModelResponse(response, request.projectId),
    },
  ];

  for (const registration of registrations) {
    ipcMain.handle(registration.channel, async (event, rawRequest) => {
      const requestId = safeRequestIdFromUnknown(rawRequest);
      try {
        assertTrustedRendererSender(event, webContents, appOrigin);
        const request = registration.validateRequest(rawRequest);
        const response = await registration.invoke(request);
        return registration.validateResponse(response, request);
      } catch (error) {
        return createRedactedErrorResponse(
          requestId,
          contractErrorCode(error, IPC_ERROR_CODES.UTILITY_UNAVAILABLE)
        );
      }
    });
  }

  return Object.freeze({
    channels: Object.freeze(registrations.map((registration) => registration.channel)),
    dispose() {
      for (const registration of registrations) {
        ipcMain.removeHandler(registration.channel);
      }
    },
  });
}

module.exports = { installProductionIpcHandlers };
