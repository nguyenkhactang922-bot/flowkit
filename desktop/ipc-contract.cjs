'use strict';

const IPC_PROTOCOL_VERSION = 1;
const UTILITY_PROTOCOL_VERSION = 1;
const STUDIO_READ_MODEL_VERSION = 1;

const CHANNELS = Object.freeze({
  GET_BRIDGE_STATUS: 'flowkit:utility:get-bridge-status',
  GET_STUDIO_APPLICATION_READ_MODEL: 'flowkit:studio:get-application-read-model',
});

const UTILITY_CAPABILITIES = Object.freeze({
  GET_BRIDGE_STATUS: 'bridge.get-status',
  GET_STUDIO_APPLICATION_READ_MODEL: 'studio.get-application-read-model',
});

const STUDIO_VIEW_SECTION_KEYS = Object.freeze([
  'authorityProvenance',
  'profileResolution',
  'storyHierarchy',
  'shotTrace',
  'stateReference',
  'jobsQaRepair',
  'ambiguityRecovery',
  'evidenceStatus',
]);

const IPC_ERROR_CODES = Object.freeze({
  ACCESS_DENIED: 'ACCESS_DENIED',
  INVALID_REQUEST: 'INVALID_REQUEST',
  INVALID_RESPONSE: 'INVALID_RESPONSE',
  UTILITY_UNAVAILABLE: 'UTILITY_UNAVAILABLE',
  UTILITY_TIMEOUT: 'UTILITY_TIMEOUT',
  APPLICATION_READ_MODEL_UNAVAILABLE: 'APPLICATION_READ_MODEL_UNAVAILABLE',
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

function assertText(value, label, maxLength = 320) {
  if (typeof value !== 'string' || !value || value !== value.trim()) {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, `${label} must be a trimmed string`);
  }
  if (value.length > maxLength || /[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(value)) {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, `${label} is invalid`);
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

function validateStudioApplicationReadModelRequest(value) {
  assertPlainObject(value, 'Studio application read-model request');
  assertExactKeys(value, ['apiVersion', 'requestId', 'projectId'], 'Studio application read-model request');
  return Object.freeze({
    apiVersion: validateVersion(value.apiVersion, IPC_PROTOCOL_VERSION, 'IPC protocol'),
    requestId: assertToken(value.requestId, 'requestId'),
    projectId: assertToken(value.projectId, 'projectId'),
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

function toUtilityStudioApplicationReadModelRequest(request) {
  const validated = validateStudioApplicationReadModelRequest(request);
  return Object.freeze({
    apiVersion: UTILITY_PROTOCOL_VERSION,
    requestId: validated.requestId,
    capability: UTILITY_CAPABILITIES.GET_STUDIO_APPLICATION_READ_MODEL,
    projectId: validated.projectId,
  });
}

function validateUtilityRequest(value) {
  assertPlainObject(value, 'utility request');
  const apiVersion = validateVersion(value.apiVersion, UTILITY_PROTOCOL_VERSION, 'utility protocol');
  const requestId = assertToken(value.requestId, 'requestId');
  if (value.capability === UTILITY_CAPABILITIES.GET_BRIDGE_STATUS) {
    assertExactKeys(value, ['apiVersion', 'requestId', 'capability'], 'utility request');
    return Object.freeze({ apiVersion, requestId, capability: value.capability });
  }
  if (value.capability === UTILITY_CAPABILITIES.GET_STUDIO_APPLICATION_READ_MODEL) {
    assertExactKeys(value, ['apiVersion', 'requestId', 'capability', 'projectId'], 'utility request');
    return Object.freeze({
      apiVersion,
      requestId,
      capability: value.capability,
      projectId: assertToken(value.projectId, 'projectId'),
    });
  }
  throw new IpcContractError(IPC_ERROR_CODES.INVALID_REQUEST, 'unknown utility capability');
}

function createBridgeStatusSuccess(requestId) {
  return Object.freeze({
    apiVersion: IPC_PROTOCOL_VERSION,
    requestId: assertToken(requestId, 'requestId'),
    ok: true,
    data: Object.freeze({
      utilityStatus: 'READY',
      utilityProtocolVersion: UTILITY_PROTOCOL_VERSION,
      capabilities: Object.freeze(Object.values(UTILITY_CAPABILITIES)),
    }),
    error: null,
  });
}

function validateCanonicalRef(value, label) {
  assertPlainObject(value, label);
  assertExactKeys(value, ['logicalId', 'versionId'], label);
  return Object.freeze({
    logicalId: assertToken(value.logicalId, `${label}.logicalId`, 240),
    versionId: assertToken(value.versionId, `${label}.versionId`, 240),
  });
}

function validateStudioViewItem(value, label) {
  assertPlainObject(value, label);
  assertExactKeys(
    value,
    ['id', 'kind', 'label', 'state', 'canonicalRef', 'authority', 'provenanceRefs'],
    label
  );
  if (!Array.isArray(value.provenanceRefs) || value.provenanceRefs.length > 32) {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, `${label}.provenanceRefs is invalid`);
  }
  return Object.freeze({
    id: assertToken(value.id, `${label}.id`, 240),
    kind: assertToken(value.kind, `${label}.kind`, 120),
    label: assertText(value.label, `${label}.label`),
    state: assertToken(value.state, `${label}.state`, 80),
    canonicalRef: value.canonicalRef === null ? null : validateCanonicalRef(value.canonicalRef, `${label}.canonicalRef`),
    authority: value.authority === null ? null : assertText(value.authority, `${label}.authority`, 240),
    provenanceRefs: Object.freeze(
      value.provenanceRefs.map((entry, index) => assertToken(entry, `${label}.provenanceRefs[${index}]`, 240))
    ),
  });
}

function validateStudioViewSection(value, label) {
  assertPlainObject(value, label);
  assertExactKeys(value, ['status', 'items'], label);
  if (!['READY', 'EMPTY', 'BLOCKED'].includes(value.status)) {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, `${label}.status is invalid`);
  }
  if (!Array.isArray(value.items) || value.items.length > 200) {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, `${label}.items is invalid`);
  }
  return Object.freeze({
    status: value.status,
    items: Object.freeze(value.items.map((item, index) => validateStudioViewItem(item, `${label}.items[${index}]`))),
  });
}

function validateStudioApplicationReadModelData(value) {
  assertPlainObject(value, 'Studio application read model');
  assertExactKeys(value, ['readModelVersion', 'sourceKind', 'project', 'sections'], 'Studio application read model');
  if (value.readModelVersion !== STUDIO_READ_MODEL_VERSION) {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, 'Studio read-model version mismatch');
  }
  if (value.sourceKind !== 'CANONICAL_APPLICATION') {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, 'Studio read-model source must be canonical application');
  }
  assertPlainObject(value.project, 'Studio read-model project');
  assertExactKeys(
    value.project,
    ['projectId', 'label', 'workflowState', 'activeProfileRef'],
    'Studio read-model project'
  );
  assertPlainObject(value.sections, 'Studio read-model sections');
  assertExactKeys(value.sections, STUDIO_VIEW_SECTION_KEYS, 'Studio read-model sections');
  const sections = {};
  for (const key of STUDIO_VIEW_SECTION_KEYS) {
    sections[key] = validateStudioViewSection(value.sections[key], `Studio read-model sections.${key}`);
  }
  return Object.freeze({
    readModelVersion: STUDIO_READ_MODEL_VERSION,
    sourceKind: 'CANONICAL_APPLICATION',
    project: Object.freeze({
      projectId: assertToken(value.project.projectId, 'Studio read-model project.projectId'),
      label: assertText(value.project.label, 'Studio read-model project.label'),
      workflowState: assertToken(value.project.workflowState, 'Studio read-model project.workflowState', 80),
      activeProfileRef:
        value.project.activeProfileRef === null
          ? null
          : validateCanonicalRef(value.project.activeProfileRef, 'Studio read-model project.activeProfileRef'),
    }),
    sections: Object.freeze(sections),
  });
}

function createStudioApplicationReadModelSuccess(requestId, data) {
  return Object.freeze({
    apiVersion: IPC_PROTOCOL_VERSION,
    requestId: assertToken(requestId, 'requestId'),
    ok: true,
    data: validateStudioApplicationReadModelData(data),
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

function validateFailureEnvelope(value, label) {
  if (value.data !== null) {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, `${label} failed response cannot include data`);
  }
  assertPlainObject(value.error, `${label} error`);
  assertExactKeys(value.error, ['code', 'message'], `${label} error`);
  if (!Object.values(IPC_ERROR_CODES).includes(value.error.code)) {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, `${label} has unknown error code`);
  }
  if (value.error.message !== 'Request could not be completed.') {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, `${label} error detail must be redacted`);
  }
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
    validateVersion(value.data.utilityProtocolVersion, UTILITY_PROTOCOL_VERSION, 'utility protocol');
    const expectedCapabilities = Object.values(UTILITY_CAPABILITIES);
    if (
      !Array.isArray(value.data.capabilities) ||
      value.data.capabilities.length !== expectedCapabilities.length ||
      expectedCapabilities.some((capability) => !value.data.capabilities.includes(capability))
    ) {
      throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, 'utility capabilities are invalid');
    }
    if (value.error !== null) {
      throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, 'successful response cannot include error');
    }
  } else {
    validateFailureEnvelope(value, 'bridge status');
  }
  return value;
}

function validateStudioApplicationReadModelResponse(value, expectedProjectId = null) {
  assertPlainObject(value, 'Studio application read-model response');
  assertExactKeys(
    value,
    ['apiVersion', 'requestId', 'ok', 'data', 'error'],
    'Studio application read-model response'
  );
  validateVersion(value.apiVersion, IPC_PROTOCOL_VERSION, 'IPC protocol');
  assertToken(value.requestId, 'requestId');
  const boundProjectId = expectedProjectId === null
    ? null
    : assertToken(expectedProjectId, 'expected projectId');
  if (typeof value.ok !== 'boolean') {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, 'response ok flag must be boolean');
  }
  if (value.ok) {
    const data = validateStudioApplicationReadModelData(value.data);
    if (boundProjectId !== null && data.project.projectId !== boundProjectId) {
      throw new IpcContractError(
        IPC_ERROR_CODES.INVALID_RESPONSE,
        'Studio read-model project binding mismatch'
      );
    }
    if (value.error !== null) {
      throw new IpcContractError(IPC_ERROR_CODES.INVALID_RESPONSE, 'successful response cannot include error');
    }
  } else {
    validateFailureEnvelope(value, 'Studio application read-model');
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
  STUDIO_READ_MODEL_VERSION,
  STUDIO_VIEW_SECTION_KEYS,
  CHANNELS,
  UTILITY_CAPABILITIES,
  IPC_ERROR_CODES,
  IpcContractError,
  validateBridgeStatusRequest,
  validateStudioApplicationReadModelRequest,
  toUtilityBridgeStatusRequest,
  toUtilityStudioApplicationReadModelRequest,
  validateUtilityRequest,
  createBridgeStatusSuccess,
  validateStudioApplicationReadModelData,
  createStudioApplicationReadModelSuccess,
  createRedactedErrorResponse,
  validateBridgeStatusResponse,
  validateStudioApplicationReadModelResponse,
  safeRequestIdFromUnknown,
  assertTrustedRendererSender,
  contractErrorCode,
};
