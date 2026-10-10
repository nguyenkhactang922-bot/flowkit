'use strict';

const IPC_PROTOCOL_VERSION = 1;
const UTILITY_PROTOCOL_VERSION = 1;

const CHANNELS = Object.freeze({
  GET_BRIDGE_STATUS: 'flowkit:utility:get-bridge-status',
});

const UTILITY_CAPABILITIES = Object.freeze({
  GET_BRIDGE_STATUS: 'bridge.get-status',
});

const IPC_ERROR_CODES = Object.freeze({
  ACCESS_DENIED: 'ACCESS_DENIED',
  INVALID_REQUEST: 'INVALID_REQUEST',
  INVALID_RESPONSE: 'INVALID_RESPONSE',
  UTILITY_UNAVAILABLE: 'UTILITY_UNAVAILABLE',
  UTILITY_TIMEOUT: 'UTILITY_TIMEOUT',
});

class IpcContractError extends Error {
  constructor(code, message) {
    super(message);
    this.name = 'IpcContractError';
    this.code = code;
  }
}

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function assertPlainObject(value, label) {
  if (!isPlainObject(value)) {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_REQUEST, `${label} must be an object`);
  }
}

function assertExactKeys(value, allowedKeys, label) {
  const actual = Object.keys(value).sort();
  const expected = [...allowedKeys].sort();
  if (actual.length !== expected.length || actual.some((key, index) => key !== expected[index])) {
    throw new IpcContractError(
      IPC_ERROR_CODES.INVALID_REQUEST,
      `${label} contains unsupported or missing fields`
    );
  }
}

function assertToken(value, label, maxLength = 160) {
  if (typeof value !== 'string' || !value || value !== value.trim()) {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_REQUEST, `${label} must be a trimmed string`);
  }
  if (value.length > maxLength || !/^[A-Za-z0-9._:-]+$/.test(value)) {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_REQUEST, `${label} has invalid characters`);
  }
  return value;
}

function validateVersion(value, expected, label) {
  if (!Number.isInteger(value) || value !== expected) {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_REQUEST, `${label} version mismatch`);
  }
  return value;
}

function validateBridgeStatusRequest(value) {
  assertPlainObject(value, 'bridge status request');
  assertExactKeys(value, ['apiVersion', 'requestId'], 'bridge status request');
  return Object.freeze({
    apiVersion: validateVersion(value.apiVersion, IPC_PROTOCOL_VERSION, 'IPC protocol'),
    requestId: assertToken(value.requestId, 'requestId'),
  });
}

function toUtilityBridgeStatusRequest(request) {
  const validated = validateBridgeStatusRequest(request);
  return Object.freeze({
    apiVersion: UTILITY_PROTOCOL_VERSION,
    requestId: validated.requestId,
    capability: UTILITY_CAPABILITIES.GET_BRIDGE_STATUS,
  });
}

function validateUtilityRequest(value) {
  assertPlainObject(value, 'utility request');
  assertExactKeys(value, ['apiVersion', 'requestId', 'capability'], 'utility request');
  const apiVersion = validateVersion(value.apiVersion, UTILITY_PROTOCOL_VERSION, 'utility protocol');
  const requestId = assertToken(value.requestId, 'requestId');
  if (value.capability !== UTILITY_CAPABILITIES.GET_BRIDGE_STATUS) {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_REQUEST, 'unknown utility capability');
  }
  return Object.freeze({ apiVersion, requestId, capability: value.capability });
}

function createBridgeStatusSuccess(requestId) {
  return Object.freeze({
    apiVersion: IPC_PROTOCOL_VERSION,
    requestId: assertToken(requestId, 'requestId'),
    ok: true,
    data: Object.freeze({
      utilityStatus: 'READY',
      utilityProtocolVersion: UTILITY_PROTOCOL_VERSION,
      capabilities: Object.freeze([UTILITY_CAPABILITIES.GET_BRIDGE_STATUS]),
    }),
    error: null,
  });
}

function createRedactedErrorResponse(requestId, code) {
  const safeRequestId = safeRequestIdFromUnknown(requestId);
  const safeCode = Object.values(IPC_ERROR_CODES).includes(code)
    ? code
    : IPC_ERROR_CODES.UTILITY_UNAVAILABLE;
  return Object.freeze({
    apiVersion: IPC_PROTOCOL_VERSION,
    requestId: safeRequestId,
    ok: false,
    data: null,
    error: Object.freeze({
      code: safeCode,
      message: 'Request could not be completed.',
    }),
  });
}

function validateBridgeStatusResponse(value) {
  assertPlainObject(value, 'bridge status response');
  assertExactKeys(value, ['apiVersion', 'requestId', 'ok', 'data', 'error'], 'bridge status response');
  validateVersion(value.apiVersion, IPC_PROTOCOL_VERSION, 'IPC protocol');
  assertToken(value.requestId, 'requestId');
  if (typeof value.ok !== 'boolean') {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, 'response ok flag must be boolean');
  }
  if (value.ok) {
    assertPlainObject(value.data, 'bridge status data');
    assertExactKeys(
      value.data,
      ['utilityStatus', 'utilityProtocolVersion', 'capabilities'],
      'bridge status data'
    );
    if (value.data.utilityStatus !== 'READY') {
      throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, 'utility status is invalid');
    }
    validateVersion(
      value.data.utilityProtocolVersion,
      UTILITY_PROTOCOL_VERSION,
      'utility protocol'
    );
    if (
      !Array.isArray(value.data.capabilities) ||
      value.data.capabilities.length !== 1 ||
      value.data.capabilities[0] !== UTILITY_CAPABILITIES.GET_BRIDGE_STATUS
    ) {
      throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, 'utility capabilities are invalid');
    }
    if (value.error !== null) {
      throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, 'successful response cannot include error');
    }
  } else {
    if (value.data !== null) {
      throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, 'failed response cannot include data');
    }
    assertPlainObject(value.error, 'bridge status error');
    assertExactKeys(value.error, ['code', 'message'], 'bridge status error');
    if (!Object.values(IPC_ERROR_CODES).includes(value.error.code)) {
      throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, 'unknown error code');
    }
    if (value.error.message !== 'Request could not be completed.') {
      throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, 'error detail must be redacted');
    }
  }
  return value;
}

function safeRequestIdFromUnknown(value) {
  if (isPlainObject(value) && typeof value.requestId === 'string') {
    return safeRequestIdFromUnknown(value.requestId);
  }
  if (typeof value === 'string' && value.length <= 160 && /^[A-Za-z0-9._:-]+$/.test(value)) {
    return value;
  }
  return 'unknown';
}

function assertTrustedRendererSender(event, expectedWebContents, appOrigin) {
  if (!event || !expectedWebContents || event.sender !== expectedWebContents) {
    throw new IpcContractError(IPC_ERROR_CODES.ACCESS_DENIED, 'renderer sender mismatch');
  }
  const frame = event.senderFrame;
  if (!frame || !expectedWebContents.mainFrame || frame !== expectedWebContents.mainFrame) {
    throw new IpcContractError(IPC_ERROR_CODES.ACCESS_DENIED, 'renderer frame mismatch');
  }
  let candidate;
  let expected;
  try {
    candidate = new URL(frame.url);
    expected = new URL(appOrigin);
  } catch (_error) {
    throw new IpcContractError(IPC_ERROR_CODES.ACCESS_DENIED, 'renderer origin invalid');
  }
  if (
    candidate.protocol !== expected.protocol ||
    candidate.hostname !== expected.hostname ||
    candidate.port !== expected.port ||
    candidate.username ||
    candidate.password
  ) {
    throw new IpcContractError(IPC_ERROR_CODES.ACCESS_DENIED, 'renderer origin mismatch');
  }
  return true;
}

function contractErrorCode(error, fallback = IPC_ERROR_CODES.UTILITY_UNAVAILABLE) {
  if (error instanceof IpcContractError && Object.values(IPC_ERROR_CODES).includes(error.code)) {
    return error.code;
  }
  return fallback;
}

module.exports = {
  IPC_PROTOCOL_VERSION,
  UTILITY_PROTOCOL_VERSION,
  CHANNELS,
  UTILITY_CAPABILITIES,
  IPC_ERROR_CODES,
  IpcContractError,
  validateBridgeStatusRequest,
  toUtilityBridgeStatusRequest,
  validateUtilityRequest,
  createBridgeStatusSuccess,
  createRedactedErrorResponse,
  validateBridgeStatusResponse,
  safeRequestIdFromUnknown,
  assertTrustedRendererSender,
  contractErrorCode,
};
