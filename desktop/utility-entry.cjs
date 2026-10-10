'use strict';

const {
  IPC_ERROR_CODES,
  createBridgeStatusSuccess,
  createRedactedErrorResponse,
  safeRequestIdFromUnknown,
  validateUtilityRequest,
} = require('./ipc-contract.cjs');

function handleUtilityMessage(rawMessage) {
  try {
    const request = validateUtilityRequest(rawMessage);
    return createBridgeStatusSuccess(request.requestId);
  } catch (_error) {
    return createRedactedErrorResponse(
      safeRequestIdFromUnknown(rawMessage),
      IPC_ERROR_CODES.INVALID_REQUEST
    );
  }
}

function installParentPortHandler(parentPort = process.parentPort) {
  if (!parentPort || typeof parentPort.on !== 'function' || typeof parentPort.postMessage !== 'function') {
    throw new Error('Production Utility requires Electron process.parentPort');
  }
  parentPort.on('message', (event) => {
    parentPort.postMessage(handleUtilityMessage(event && event.data));
  });
}

if (require.main === module) {
  installParentPortHandler();
}

module.exports = {
  handleUtilityMessage,
  installParentPortHandler,
};
