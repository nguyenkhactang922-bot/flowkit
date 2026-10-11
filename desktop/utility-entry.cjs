'use strict';

const {
  IPC_ERROR_CODES,
  UTILITY_CAPABILITIES,
  createBridgeStatusSuccess,
  createRedactedErrorResponse,
  createStudioApplicationReadModelSuccess,
  safeRequestIdFromUnknown,
  validateUtilityRequest,
} = require('./ipc-contract.cjs');

function unavailableReadModelResponse(requestId) {
  return createRedactedErrorResponse(
    requestId,
    IPC_ERROR_CODES.APPLICATION_READ_MODEL_UNAVAILABLE
  );
}

function handleUtilityMessage(rawMessage, { applicationReadModelProvider = null } = {}) {
  let request;
  try {
    request = validateUtilityRequest(rawMessage);
  } catch (_error) {
    return createRedactedErrorResponse(
      safeRequestIdFromUnknown(rawMessage),
      IPC_ERROR_CODES.INVALID_REQUEST
    );
  }

  if (request.capability === UTILITY_CAPABILITIES.GET_BRIDGE_STATUS) {
    return createBridgeStatusSuccess(request.requestId);
  }

  if (request.capability === UTILITY_CAPABILITIES.GET_STUDIO_APPLICATION_READ_MODEL) {
    if (typeof applicationReadModelProvider !== 'function') {
      return unavailableReadModelResponse(request.requestId);
    }
    try {
      const result = applicationReadModelProvider({
        projectId: request.projectId,
        requestId: request.requestId,
      });
      if (result && typeof result.then === 'function') {
        return Promise.resolve(result)
          .then((data) => createStudioApplicationReadModelSuccess(request.requestId, data))
          .catch(() => unavailableReadModelResponse(request.requestId));
      }
      return createStudioApplicationReadModelSuccess(request.requestId, result);
    } catch (_error) {
      return unavailableReadModelResponse(request.requestId);
    }
  }

  return createRedactedErrorResponse(
    request.requestId,
    IPC_ERROR_CODES.INVALID_REQUEST
  );
}

function installParentPortHandler(
  parentPort = process.parentPort,
  { applicationReadModelProvider = null } = {}
) {
  if (!parentPort || typeof parentPort.on !== 'function' || typeof parentPort.postMessage !== 'function') {
    throw new Error('Production Utility requires Electron process.parentPort');
  }
  parentPort.on('message', (event) => {
    Promise.resolve(
      handleUtilityMessage(event && event.data, { applicationReadModelProvider })
    ).then((response) => parentPort.postMessage(response));
  });
}

if (require.main === module) {
  installParentPortHandler();
}

module.exports = {
  handleUtilityMessage,
  installParentPortHandler,
};
