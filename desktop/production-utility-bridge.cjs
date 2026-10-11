'use strict';

const crypto = require('node:crypto');

const {
  IPC_ERROR_CODES,
  IpcContractError,
  toUtilityBridgeStatusRequest,
  validateBridgeStatusResponse,
} = require('./ipc-contract.cjs');

const UTILITY_CREDENTIAL_MESSAGE_TYPES = Object.freeze({
  ISSUE_LEASE: 'host-security:credential-lease:issue',
  REDEEM_LEASE: 'host-security:credential-lease:redeem',
  RESPONSE: 'host-security:credential-lease:response',
});

function assertToken(value, label, maxLength = 256) {
  if (typeof value !== 'string' || !value || value !== value.trim()) {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_REQUEST, `${label} must be a non-empty trimmed string`);
  }
  if (value.length > maxLength || !/^[A-Za-z0-9._:-]+$/.test(value)) {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_REQUEST, `${label} has invalid characters`);
  }
  return value;
}

function assertExactKeys(value, expectedKeys) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_REQUEST, 'credential utility message must be an object');
  }
  const actual = Object.keys(value).sort();
  const expected = [...expectedKeys].sort();
  if (actual.length !== expected.length || actual.some((key, index) => key !== expected[index])) {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_REQUEST, 'credential utility message has unsupported or missing fields');
  }
}

function validateCredentialUtilityMessage(raw) {
  if (!raw || typeof raw !== 'object') {
    throw new IpcContractError(IPC_ERROR_CODES.INVALID_REQUEST, 'credential utility message must be an object');
  }
  if (raw.type === UTILITY_CREDENTIAL_MESSAGE_TYPES.ISSUE_LEASE) {
    assertExactKeys(raw, [
      'type',
      'requestId',
      'credentialId',
      'provider',
      'operation',
      'correlationId',
      'ttlMs',
    ]);
    if (!Number.isInteger(raw.ttlMs)) {
      throw new IpcContractError(IPC_ERROR_CODES.INVALID_REQUEST, 'ttlMs must be an integer');
    }
    return Object.freeze({
      type: raw.type,
      requestId: assertToken(raw.requestId, 'requestId'),
      credentialId: assertToken(raw.credentialId, 'credentialId'),
      provider: assertToken(raw.provider, 'provider'),
      operation: assertToken(raw.operation, 'operation'),
      correlationId: assertToken(raw.correlationId, 'correlationId'),
      ttlMs: raw.ttlMs,
    });
  }
  if (raw.type === UTILITY_CREDENTIAL_MESSAGE_TYPES.REDEEM_LEASE) {
    assertExactKeys(raw, [
      'type',
      'requestId',
      'leaseId',
      'provider',
      'operation',
      'correlationId',
    ]);
    return Object.freeze({
      type: raw.type,
      requestId: assertToken(raw.requestId, 'requestId'),
      leaseId: assertToken(raw.leaseId, 'leaseId'),
      provider: assertToken(raw.provider, 'provider'),
      operation: assertToken(raw.operation, 'operation'),
      correlationId: assertToken(raw.correlationId, 'correlationId'),
    });
  }
  throw new IpcContractError(IPC_ERROR_CODES.INVALID_REQUEST, 'unknown credential utility message type');
}

function safeRequestId(raw) {
  try {
    return assertToken(raw && raw.requestId, 'requestId');
  } catch (_error) {
    return 'credential-request-invalid';
  }
}

class ProductionUtilityBridge {
  constructor({
    utilityProcess,
    entryPath,
    requestTimeoutMs = 5000,
    credentialBroker = null,
    randomUUID = () => crypto.randomUUID(),
  }) {
    if (!utilityProcess || typeof utilityProcess.fork !== 'function') {
      throw new TypeError('utilityProcess.fork is required');
    }
    if (typeof entryPath !== 'string' || !entryPath.trim()) {
      throw new TypeError('entryPath is required');
    }
    if (!Number.isInteger(requestTimeoutMs) || requestTimeoutMs < 100 || requestTimeoutMs > 60000) {
      throw new TypeError('requestTimeoutMs must be an integer between 100 and 60000');
    }
    if (credentialBroker !== null) {
      for (const method of ['registerUtilitySession', 'revokeUtilitySession', 'issueLease', 'redeemLease']) {
        if (typeof credentialBroker[method] !== 'function') {
          throw new TypeError(`credentialBroker.${method} is required`);
        }
      }
    }
    if (typeof randomUUID !== 'function') {
      throw new TypeError('randomUUID is required');
    }
    this.utilityProcess = utilityProcess;
    this.entryPath = entryPath;
    this.requestTimeoutMs = requestTimeoutMs;
    this.credentialBroker = credentialBroker;
    this.randomUUID = randomUUID;
    this.child = null;
    this.pending = new Map();
    this.lastExit = null;
    this.utilityInstanceId = null;
    this.credentialSession = null;
  }

  start() {
    if (this.child) {
      return this.child;
    }
    const child = this.utilityProcess.fork(this.entryPath);
    if (!child || typeof child.postMessage !== 'function' || typeof child.on !== 'function') {
      throw new IpcContractError(
        IPC_ERROR_CODES.UTILITY_UNAVAILABLE,
        'utility process did not provide the expected transport'
      );
    }
    this.child = child;
    this.utilityInstanceId = `utility-${assertToken(this.randomUUID(), 'generated utility instance id')}`;
    child.on('message', (message) => this._onMessage(message));
    child.on('exit', (code) => this._onExit(code));
    return child;
  }

  async getBridgeStatus(rendererRequest) {
    const utilityRequest = toUtilityBridgeStatusRequest(rendererRequest);
    this.start();
    return this._sendAndWait(utilityRequest);
  }

  authorizeCredentialScope({ allowedProviders, allowedOperations }) {
    if (!this.credentialBroker) {
      throw new IpcContractError(IPC_ERROR_CODES.ACCESS_DENIED, 'credential broker unavailable');
    }
    this.start();
    this._revokeCredentialSession();
    const sessionToken = `session-${assertToken(this.randomUUID(), 'generated session token')}`;
    const metadata = this.credentialBroker.registerUtilitySession({
      utilityInstanceId: this.utilityInstanceId,
      sessionToken,
      allowedProviders,
      allowedOperations,
    });
    this.credentialSession = Object.freeze({
      utilityInstanceId: this.utilityInstanceId,
      sessionToken,
      allowedProviders: metadata.allowedProviders,
      allowedOperations: metadata.allowedOperations,
    });
    return Object.freeze({
      utilityInstanceId: metadata.utilityInstanceId,
      allowedProviders: metadata.allowedProviders,
      allowedOperations: metadata.allowedOperations,
      registeredAt: metadata.registeredAt,
    });
  }

  close() {
    this._revokeCredentialSession();
    const child = this.child;
    this.child = null;
    this.utilityInstanceId = null;
    if (child && typeof child.kill === 'function') {
      child.kill();
    }
    this._rejectAll(
      new IpcContractError(IPC_ERROR_CODES.UTILITY_UNAVAILABLE, 'utility bridge closed')
    );
  }

  _sendAndWait(request) {
    if (!this.child) {
      throw new IpcContractError(IPC_ERROR_CODES.UTILITY_UNAVAILABLE, 'utility process unavailable');
    }
    if (this.pending.has(request.requestId)) {
      throw new IpcContractError(IPC_ERROR_CODES.INVALID_REQUEST, 'duplicate requestId');
    }

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.pending.delete(request.requestId);
        reject(new IpcContractError(IPC_ERROR_CODES.UTILITY_TIMEOUT, 'utility request timed out'));
      }, this.requestTimeoutMs);

      this.pending.set(request.requestId, { resolve, reject, timeout });
      try {
        this.child.postMessage(request);
      } catch (error) {
        clearTimeout(timeout);
        this.pending.delete(request.requestId);
        reject(
          new IpcContractError(
            IPC_ERROR_CODES.UTILITY_UNAVAILABLE,
            error instanceof Error ? error.message : 'utility postMessage failed'
          )
        );
      }
    });
  }

  _onMessage(message) {
    if (
      message &&
      (message.type === UTILITY_CREDENTIAL_MESSAGE_TYPES.ISSUE_LEASE ||
        message.type === UTILITY_CREDENTIAL_MESSAGE_TYPES.REDEEM_LEASE)
    ) {
      void this._handleCredentialMessage(message);
      return;
    }

    let validated;
    try {
      validated = validateBridgeStatusResponse(message);
    } catch (error) {
      const requestId = message && typeof message.requestId === 'string' ? message.requestId : null;
      if (requestId && this.pending.has(requestId)) {
        const pending = this.pending.get(requestId);
        clearTimeout(pending.timeout);
        this.pending.delete(requestId);
        pending.reject(
          new IpcContractError(
            IPC_ERROR_CODES.INVALID_RESPONSE,
            error instanceof Error ? error.message : 'invalid utility response'
          )
        );
      }
      return;
    }

    const pending = this.pending.get(validated.requestId);
    if (!pending) {
      return;
    }
    clearTimeout(pending.timeout);
    this.pending.delete(validated.requestId);
    pending.resolve(validated);
  }

  async _handleCredentialMessage(rawMessage) {
    let requestId = safeRequestId(rawMessage);
    try {
      const message = validateCredentialUtilityMessage(rawMessage);
      requestId = message.requestId;
      if (!this.credentialBroker || !this.credentialSession || !this.child) {
        throw new IpcContractError(IPC_ERROR_CODES.ACCESS_DENIED, 'credential session unavailable');
      }
      const scope = this.credentialSession;
      if (message.type === UTILITY_CREDENTIAL_MESSAGE_TYPES.ISSUE_LEASE) {
        const lease = await this.credentialBroker.issueLease({
          utilityInstanceId: scope.utilityInstanceId,
          sessionToken: scope.sessionToken,
          credentialId: message.credentialId,
          provider: message.provider,
          operation: message.operation,
          correlationId: message.correlationId,
          ttlMs: message.ttlMs,
        });
        this._postCredentialResponse({
          type: UTILITY_CREDENTIAL_MESSAGE_TYPES.RESPONSE,
          requestId,
          ok: true,
          data: Object.freeze({ lease }),
        });
        return;
      }

      const redeemed = await this.credentialBroker.redeemLease({
        leaseId: message.leaseId,
        utilityInstanceId: scope.utilityInstanceId,
        sessionToken: scope.sessionToken,
        provider: message.provider,
        operation: message.operation,
        correlationId: message.correlationId,
      });
      this._postCredentialResponse({
        type: UTILITY_CREDENTIAL_MESSAGE_TYPES.RESPONSE,
        requestId,
        ok: true,
        data: Object.freeze({ lease: redeemed.lease, secret: redeemed.secret }),
      });
    } catch (error) {
      this._postCredentialResponse({
        type: UTILITY_CREDENTIAL_MESSAGE_TYPES.RESPONSE,
        requestId,
        ok: false,
        error: Object.freeze({
          code:
            error && typeof error.code === 'string'
              ? error.code
              : IPC_ERROR_CODES.INVALID_REQUEST,
        }),
      });
    }
  }

  _postCredentialResponse(response) {
    if (!this.child) {
      return;
    }
    try {
      this.child.postMessage(Object.freeze(response));
    } catch (_error) {
      this._revokeCredentialSession();
    }
  }

  _onExit(code) {
    this.lastExit = code;
    this._revokeCredentialSession();
    this.child = null;
    this.utilityInstanceId = null;
    this._rejectAll(
      new IpcContractError(IPC_ERROR_CODES.UTILITY_UNAVAILABLE, 'utility process exited')
    );
  }

  _revokeCredentialSession() {
    if (this.credentialBroker && this.credentialSession) {
      this.credentialBroker.revokeUtilitySession(this.credentialSession.utilityInstanceId);
    }
    this.credentialSession = null;
  }

  _rejectAll(error) {
    for (const pending of this.pending.values()) {
      clearTimeout(pending.timeout);
      pending.reject(error);
    }
    this.pending.clear();
  }
}

module.exports = {
  ProductionUtilityBridge,
  UTILITY_CREDENTIAL_MESSAGE_TYPES,
  validateCredentialUtilityMessage,
};
