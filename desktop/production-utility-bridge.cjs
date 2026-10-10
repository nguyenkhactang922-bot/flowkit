'use strict';

const {
  IPC_ERROR_CODES,
  IpcContractError,
  toUtilityBridgeStatusRequest,
  validateBridgeStatusResponse,
} = require('./ipc-contract.cjs');

class ProductionUtilityBridge {
  constructor({ utilityProcess, entryPath, requestTimeoutMs = 5000 }) {
    if (!utilityProcess || typeof utilityProcess.fork !== 'function') {
      throw new TypeError('utilityProcess.fork is required');
    }
    if (typeof entryPath !== 'string' || !entryPath.trim()) {
      throw new TypeError('entryPath is required');
    }
    if (!Number.isInteger(requestTimeoutMs) || requestTimeoutMs < 100 || requestTimeoutMs > 60000) {
      throw new TypeError('requestTimeoutMs must be an integer between 100 and 60000');
    }
    this.utilityProcess = utilityProcess;
    this.entryPath = entryPath;
    this.requestTimeoutMs = requestTimeoutMs;
    this.child = null;
    this.pending = new Map();
    this.lastExit = null;
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
    child.on('message', (message) => this._onMessage(message));
    child.on('exit', (code) => this._onExit(code));
    return child;
  }

  async getBridgeStatus(rendererRequest) {
    const utilityRequest = toUtilityBridgeStatusRequest(rendererRequest);
    this.start();
    return this._sendAndWait(utilityRequest);
  }

  close() {
    const child = this.child;
    this.child = null;
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

  _onExit(code) {
    this.lastExit = code;
    this.child = null;
    this._rejectAll(
      new IpcContractError(IPC_ERROR_CODES.UTILITY_UNAVAILABLE, 'utility process exited')
    );
  }

  _rejectAll(error) {
    for (const pending of this.pending.values()) {
      clearTimeout(pending.timeout);
      pending.reject(error);
    }
    this.pending.clear();
  }
}

module.exports = { ProductionUtilityBridge };
