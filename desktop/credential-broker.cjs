'use strict';

const crypto = require('node:crypto');
const fs = require('node:fs/promises');
const path = require('node:path');

const CREDENTIAL_BROKER_VERSION = 1;
const DEFAULT_LEASE_TTL_MS = 10_000;
const MAX_LEASE_TTL_MS = 60_000;
const VAULT_SCHEMA_VERSION = 1;

const CREDENTIAL_STATUS = Object.freeze({
  ACTIVE: 'ACTIVE',
  REVOKED: 'REVOKED',
});

const CREDENTIAL_ERROR_CODES = Object.freeze({
  INVALID_REQUEST: 'INVALID_REQUEST',
  CREDENTIAL_NOT_FOUND: 'CREDENTIAL_NOT_FOUND',
  CREDENTIAL_REVOKED: 'CREDENTIAL_REVOKED',
  CREDENTIAL_PROVIDER_MISMATCH: 'CREDENTIAL_PROVIDER_MISMATCH',
  CREDENTIAL_BACKEND_UNAVAILABLE: 'CREDENTIAL_BACKEND_UNAVAILABLE',
  CREDENTIAL_INSECURE_BACKEND: 'CREDENTIAL_INSECURE_BACKEND',
  UTILITY_AUTH_FAILED: 'UTILITY_AUTH_FAILED',
  PROVIDER_SCOPE_DENIED: 'PROVIDER_SCOPE_DENIED',
  OPERATION_SCOPE_DENIED: 'OPERATION_SCOPE_DENIED',
  LEASE_NOT_FOUND: 'LEASE_NOT_FOUND',
  LEASE_EXPIRED: 'LEASE_EXPIRED',
  LEASE_REPLAY_DENIED: 'LEASE_REPLAY_DENIED',
  LEASE_REVOKED: 'LEASE_REVOKED',
  LEASE_STALE_AFTER_ROTATION: 'LEASE_STALE_AFTER_ROTATION',
  VAULT_CORRUPT: 'VAULT_CORRUPT',
});

class CredentialBrokerError extends Error {
  constructor(code, message = 'Credential request could not be completed.') {
    super(message);
    this.name = 'CredentialBrokerError';
    this.code = code;
  }
}

function assertPlainObject(value, label) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    throw new CredentialBrokerError(
      CREDENTIAL_ERROR_CODES.INVALID_REQUEST,
      `${label} must be an object`
    );
  }
  return value;
}

function assertToken(value, label, maxLength = 160) {
  if (typeof value !== 'string' || !value || value !== value.trim()) {
    throw new CredentialBrokerError(
      CREDENTIAL_ERROR_CODES.INVALID_REQUEST,
      `${label} must be a non-empty trimmed string`
    );
  }
  if (value.length > maxLength || !/^[A-Za-z0-9._:-]+$/.test(value)) {
    throw new CredentialBrokerError(
      CREDENTIAL_ERROR_CODES.INVALID_REQUEST,
      `${label} has invalid characters`
    );
  }
  return value;
}

function assertLabel(value, label = 'label') {
  if (typeof value !== 'string' || !value || value !== value.trim() || value.length > 160) {
    throw new CredentialBrokerError(
      CREDENTIAL_ERROR_CODES.INVALID_REQUEST,
      `${label} must be a non-empty trimmed string up to 160 characters`
    );
  }
  if(/[\u0000-\u001f\u007f]/.test(value)) {
    throw new CredentialBrokerError(
      CREDENTIAL_ERROR_CODES.INVALID_REQUEST,
      `${label} contains control characters`
    );
  }
  return value;
}

function assertSecret(value) {
  if (typeof value !== 'string' || value.length === 0) {
    throw new CredentialBrokerError(
      CREDENTIAL_ERROR_CODES.INVALID_REQUEST,
      'secret must be a non-empty string'
    );
  }
  if (value.length > 65_536) {
    throw new CredentialBrokerError(
      CREDENTIAL_ERROR_CODES.INVALID_REQUEST,
      'secret exceeds maximum supported length'
    );
  }
  return value;
}

function assertTokenSet(values, label) {
  if (!Array.isArray(values) || values.length === 0) {
    throw new CredentialBrokerError(
      CREDENTIAL_ERROR_CODES.INVALID_REQUEST,
      `${label} must contain at least one value`
    );
  }
  const normalized = values.map((value) => assertToken(value, `${label} entry`));
  if (new Set(normalized).size !== normalized.length) {
    throw new CredentialBrokerError(
      CREDENTIAL_ERROR_CODES.INVALID_REQUEST,
      `${label} must not contain duplicates`
    );
  }
  return Object.freeze([...normalized]);
}

function immutableMetadata(record) {
  return Object.freeze({
    credentialId: record.credentialId,
    provider: record.provider,
    label: record.label,
    credentialVersion: record.credentialVersion,
    status: record.status,
    createdAt: record.createdAt,
    rotatedAt: record.rotatedAt || null,
    revokedAt: record.revokedAt || null,
  });
}

function immutableLeaseMetadata(lease) {
  return Object.freeze({
    leaseId: lease.leaseId,
    credentialId: lease.credentialId,
    credentialVersion: lease.credentialVersion,
    provider: lease.provider,
    operation: lease.operation,
    utilityInstanceId: lease.utilityInstanceId,
    correlationId: lease.correlationId,
    issuedAt: lease.issuedAt,
    expiresAt: lease.expiresAt,
    singleUse: true,
  });
}

function normalizeEncryptedPayload(value) {
  if (Buffer.isBuffer(value)) {
    return value;
  }
  if (value instanceof Uint8Array) {
    return Buffer.from(value);
  }
  throw new CredentialBrokerError(
    CREDENTIAL_ERROR_CODES.CREDENTIAL_BACKEND_UNAVAILABLE,
    'safeStorage returned an invalid encrypted payload'
  );
}

class SafeStorageCredentialBroker {
  constructor({
    safeStorage,
    vaultPath,
    fsPromises = fs,
    now = () => Date.now(),
    randomUUID = () => crypto.randomUUID(),
    platform = process.platform,
    defaultLeaseTtlMs = DEFAULT_LEASE_TTL_MS,
    maxLeaseTtlMs = MAX_LEASE_TTL_MS,
  }) {
    if (!safeStorage || typeof safeStorage.isEncryptionAvailable !== 'function') {
      throw new TypeError('safeStorage with isEncryptionAvailable() is required');
    }
    if (typeof vaultPath !== 'string' || !vaultPath.trim()) {
      throw new TypeError('vaultPath is required');
    }
    if (!fsPromises || typeof fsPromises.readFile !== 'function' || typeof fsPromises.writeFile !== 'function') {
      throw new TypeError('fsPromises-compatible implementation is required');
    }
    if (typeof now !== 'function' || typeof randomUUID !== 'function') {
      throw new TypeError('now/randomUUID functions are required');
    }
    if (!Number.isInteger(defaultLeaseTtlMs) || defaultLeaseTtlMs < 100) {
      throw new TypeError('defaultLeaseTtlMs must be an integer >= 100');
    }
    if (!Number.isInteger(maxLeaseTtlMs) || maxLeaseTtlMs < defaultLeaseTtlMs) {
      throw new TypeError('maxLeaseTtlMs must be an integer >= defaultLeaseTtlMs');
    }

    this.safeStorage = safeStorage;
    this.vaultPath = path.resolve(vaultPath);
    this.fs = fsPromises;
    this.now = now;
    this.randomUUID = randomUUID;
    this.platform = platform;
    this.defaultLeaseTtlMs = defaultLeaseTtlMs;
    this.maxLeaseTtlMs = maxLeaseTtlMs;
    this.credentials = new Map();
    this.utilitySessions = new Map();
    this.leases = new Map();
    this.loaded = false;
  }

  async putCredential({ credentialId, provider, label, secret }) {
    credentialId = assertToken(credentialId, 'credentialId');
    provider = assertToken(provider, 'provider');
    label = assertLabel(label);
    secret = assertSecret(secret);
    await this._ensureLoaded();
    this._assertSecureStorage();

    const existing = this.credentials.get(credentialId) || null;
    if (existing && existing.provider !== provider) {
      throw new CredentialBrokerError(
        CREDENTIAL_ERROR_CODES.CREDENTIAL_PROVIDER_MISMATCH,
        'credential provider cannot change during rotation'
      );
    }

    const encrypted = await this._encrypt(secret);
    const timestamp = new Date(this._nowMs()).toISOString();
    const credentialVersion = existing ? existing.credentialVersion + 1 : 1;
    const record = Object.freeze({
      credentialId,
      provider,
      label,
      credentialVersion,
      status: CREDENTIAL_STATUS.ACTIVE,
      encryptedPayloadB64: encrypted.toString('base64'),
      createdAt: existing ? existing.createdAt : timestamp,
      rotatedAt: existing ? timestamp : null,
      revokedAt: null,
    });

    this.credentials.set(credentialId, record);
    if (existing) {
      this._invalidateCredentialLeases(credentialId, 'CREDENTIAL_ROTATED');
    }
    await this._persistVault();
    return immutableMetadata(record);
  }

  async revokeCredential({ credentialId }) {
    credentialId = assertToken(credentialId, 'credentialId');
    await this._ensureLoaded();
    const existing = this.credentials.get(credentialId);
    if (!existing) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.CREDENTIAL_NOT_FOUND);
    }
    if (existing.status === CREDENTIAL_STATUS.REVOKED) {
      return immutableMetadata(existing);
    }
    const record = Object.freeze({
      ...existing,
      status: CREDENTIAL_STATUS.REVOKED,
      revokedAt: new Date(this._nowMs()).toISOString(),
    });
    this.credentials.set(credentialId, record);
    this._invalidateCredentialLeases(credentialId, 'CREDENTIAL_REVOKED');
    await this._persistVault();
    return immutableMetadata(record);
  }

  async listCredentialMetadata() {
    await this._ensureLoaded();
    return Object.freeze(
      [...this.credentials.values()]
        .sort((left, right) => left.credentialId.localeCompare(right.credentialId))
        .map((record) => immutableMetadata(record))
    );
  }

  registerUtilitySession({
    utilityInstanceId,
    sessionToken,
    allowedProviders,
    allowedOperations,
  }) {
    utilityInstanceId = assertToken(utilityInstanceId, 'utilityInstanceId');
    sessionToken = assertToken(sessionToken, 'sessionToken', 256);
    const providers = assertTokenSet(allowedProviders, 'allowedProviders');
    const operations = assertTokenSet(allowedOperations, 'allowedOperations');
    if (this.utilitySessions.has(utilityInstanceId)) {
      throw new CredentialBrokerError(
        CREDENTIAL_ERROR_CODES.UTILITY_AUTH_FAILED,
        'utility instance already registered'
      );
    }
    const session = Object.freeze({
      utilityInstanceId,
      sessionToken,
      allowedProviders: providers,
      allowedOperations: operations,
      registeredAt: this._nowMs(),
    });
    this.utilitySessions.set(utilityInstanceId, session);
    return Object.freeze({
      utilityInstanceId,
      allowedProviders: providers,
      allowedOperations: operations,
      registeredAt: session.registeredAt,
    });
  }

  revokeUtilitySession(utilityInstanceId) {
    utilityInstanceId = assertToken(utilityInstanceId, 'utilityInstanceId');
    const existed = this.utilitySessions.delete(utilityInstanceId);
    let revokedLeaseCount = 0;
    for (const lease of this.leases.values()) {
      if (lease.utilityInstanceId === utilityInstanceId && !lease.consumedAt && !lease.revokedAt) {
        lease.revokedAt = this._nowMs();
        lease.revocationReason = 'UTILITY_SESSION_REVOKED';
        revokedLeaseCount += 1;
      }
    }
    return Object.freeze({ utilityInstanceId, existed, revokedLeaseCount });
  }

  async issueLease({
    utilityInstanceId,
    sessionToken,
    credentialId,
    provider,
    operation,
    correlationId,
    ttlMs = this.defaultLeaseTtlMs,
  }) {
    utilityInstanceId = assertToken(utilityInstanceId, 'utilityInstanceId');
    sessionToken = assertToken(sessionToken, 'sessionToken', 256);
    credentialId = assertToken(credentialId, 'credentialId');
    provider = assertToken(provider, 'provider');
    operation = assertToken(operation, 'operation');
    correlationId = assertToken(correlationId, 'correlationId');
    if (!Number.isInteger(ttlMs) || ttlMs < 100 || ttlMs > this.maxLeaseTtlMs) {
      throw new CredentialBrokerError(
        CREDENTIAL_ERROR_CODES.INVALID_REQUEST,
        'ttlMs is outside the allowed lease range'
      );
    }

    await this._ensureLoaded();
    this._assertSecureStorage();
    this._assertUtilityScope({ utilityInstanceId, sessionToken, provider, operation });
    const credential = this._activeCredential(credentialId, provider);
    const issuedAt = this._nowMs();
    const lease = {
      leaseId: assertToken(this.randomUUID(), 'generated leaseId'),
      credentialId,
      credentialVersion: credential.credentialVersion,
      provider,
      operation,
      utilityInstanceId,
      correlationId,
      issuedAt,
      expiresAt: issuedAt + ttlMs,
      consumedAt: null,
      revokedAt: null,
      revocationReason: null,
    };
    if (this.leases.has(lease.leaseId)) {
      throw new CredentialBrokerError(
        CREDENTIAL_ERROR_CODES.INVALID_REQUEST,
        'generated lease identity collision'
      );
    }
    this.leases.set(lease.leaseId, lease);
    return immutableLeaseMetadata(lease);
  }

  async redeemLease({
    leaseId,
    utilityInstanceId,
    sessionToken,
    provider,
    operation,
    correlationId,
  }) {
    leaseId = assertToken(leaseId, 'leaseId');
    utilityInstanceId = assertToken(utilityInstanceId, 'utilityInstanceId');
    sessionToken = assertToken(sessionToken, 'sessionToken', 256);
    provider = assertToken(provider, 'provider');
    operation = assertToken(operation, 'operation');
    correlationId = assertToken(correlationId, 'correlationId');

    await this._ensureLoaded();
    this._assertSecureStorage();
    this._assertUtilityScope({ utilityInstanceId, sessionToken, provider, operation });
    const lease = this.leases.get(leaseId);
    if (!lease) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.LEASE_NOT_FOUND);
    }
    this._assertLeaseScope(lease, { utilityInstanceId, provider, operation, correlationId });
    if (lease.consumedAt !== null) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.LEASE_REPLAY_DENIED);
    }
    if (lease.revokedAt !== null) {
      const code = lease.revocationReason === 'CREDENTIAL_ROTATED'
        ? CREDENTIAL_ERROR_CODES.LEASE_STALE_AFTER_ROTATION
        : CREDENTIAL_ERROR_CODES.LEASE_REVOKED;
      throw new CredentialBrokerError(code);
    }
    if (this._nowMs() >= lease.expiresAt) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.LEASE_EXPIRED);
    }

    const credential = this.credentials.get(lease.credentialId);
    if (!credential) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.CREDENTIAL_NOT_FOUND);
    }
    if (credential.status !== CREDENTIAL_STATUS.ACTIVE) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.CREDENTIAL_REVOKED);
    }
    if (credential.provider !== lease.provider) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.CREDENTIAL_PROVIDER_MISMATCH);
    }
    if (credential.credentialVersion !== lease.credentialVersion) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.LEASE_STALE_AFTER_ROTATION);
    }

    // Consume before decrypt: a backend failure must not make a one-use lease replayable.
    lease.consumedAt = this._nowMs();
    const encrypted = Buffer.from(credential.encryptedPayloadB64, 'base64');
    const secret = await this._decrypt(encrypted);
    return Object.freeze({
      lease: immutableLeaseMetadata(lease),
      secret,
    });
  }

  close() {
    for (const utilityInstanceId of [...this.utilitySessions.keys()]) {
      this.revokeUtilitySession(utilityInstanceId);
    }
    this.utilitySessions.clear();
  }

  async _ensureLoaded() {
    if (this.loaded) {
      return;
    }
    let raw;
    try {
      raw = await this.fs.readFile(this.vaultPath, 'utf8');
    } catch (error) {
      if (error && error.code === 'ENOENT') {
        this.loaded = true;
        return;
      }
      throw error;
    }

    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch (_error) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.VAULT_CORRUPT);
    }
    if (
      !parsed ||
      parsed.schemaVersion !== VAULT_SCHEMA_VERSION ||
      !Array.isArray(parsed.credentials)
    ) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.VAULT_CORRUPT);
    }

    const next = new Map();
    for (const rawRecord of parsed.credentials) {
      const record = this._validatePersistedRecord(rawRecord);
      if (next.has(record.credentialId)) {
        throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.VAULT_CORRUPT);
      }
      next.set(record.credentialId, Object.freeze(record));
    }
    this.credentials = next;
    this.loaded = true;
  }

  _validatePersistedRecord(rawRecord) {
    assertPlainObject(rawRecord, 'credential record');
    const expectedKeys = [
      'credentialId',
      'provider',
      'label',
      'credentialVersion',
      'status',
      'encryptedPayloadB64',
      'createdAt',
      'rotatedAt',
      'revokedAt',
    ].sort();
    const actualKeys = Object.keys(rawRecord).sort();
    if (actualKeys.length !== expectedKeys.length || actualKeys.some((key, index) => key !== expectedKeys[index])) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.VAULT_CORRUPT);
    }
    assertToken(rawRecord.credentialId, 'credentialId');
    assertToken(rawRecord.provider, 'provider');
    assertLabel(rawRecord.label);
    if (!Number.isInteger(rawRecord.credentialVersion) || rawRecord.credentialVersion < 1) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.VAULT_CORRUPT);
    }
    if (!Object.values(CREDENTIAL_STATUS).includes(rawRecord.status)) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.VAULT_CORRUPT);
    }
    if (typeof rawRecord.encryptedPayloadB64 !== 'string' || !rawRecord.encryptedPayloadB64) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.VAULT_CORRUPT);
    }
    if (!Buffer.from(rawRecord.encryptedPayloadB64, 'base64').length) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.VAULT_CORRUPT);
    }
    for (const key of ['createdAt', 'rotatedAt', 'revokedAt']) {
      if (rawRecord[key] !== null && (typeof rawRecord[key] !== 'string' || Number.isNaN(Date.parse(rawRecord[key])))) {
        throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.VAULT_CORRUPT);
      }
    }
    return { ...rawRecord };
  }

  async _persistVault() {
    await this.fs.mkdir(path.dirname(this.vaultPath), { recursive: true });
    const payload = JSON.stringify(
      {
        schemaVersion: VAULT_SCHEMA_VERSION,
        credentials: [...this.credentials.values()].sort((a, b) => a.credentialId.localeCompare(b.credentialId)),
      },
      null,
      2
    );
    const tempPath = `${this.vaultPath}.tmp-${assertToken(this.randomUUID(), 'generated temp id')}`;
    try {
      await this.fs.writeFile(tempPath, payload, { encoding: 'utf8', mode: 0o600 });
      await this.fs.rename(tempPath, this.vaultPath);
    } catch (error) {
      try {
        await this.fs.unlink(tempPath);
      } catch (_cleanupError) {
        // Best-effort cleanup only; never replace the original error.
      }
      throw error;
    }
  }

  _assertSecureStorage() {
    let available = false;
    try {
      available = this.safeStorage.isEncryptionAvailable() === true;
    } catch (_error) {
      available = false;
    }
    if (!available) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.CREDENTIAL_BACKEND_UNAVAILABLE);
    }
    if (
      this.platform === 'linux' &&
      typeof this.safeStorage.getSelectedStorageBackend === 'function' &&
      this.safeStorage.getSelectedStorageBackend() === 'basic_text'
    ) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.CREDENTIAL_INSECURE_BACKEND);
    }
  }

  async _encrypt(secret) {
    try {
      if (typeof this.safeStorage.encryptStringAsync === 'function') {
        return normalizeEncryptedPayload(await this.safeStorage.encryptStringAsync(secret));
      }
      if (typeof this.safeStorage.encryptString === 'function') {
        return normalizeEncryptedPayload(this.safeStorage.encryptString(secret));
      }
    } catch (_error) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.CREDENTIAL_BACKEND_UNAVAILABLE);
    }
    throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.CREDENTIAL_BACKEND_UNAVAILABLE);
  }

  async _decrypt(encrypted) {
    try {
      if (typeof this.safeStorage.decryptStringAsync === 'function') {
        const value = await this.safeStorage.decryptStringAsync(encrypted);
        return assertSecret(value);
      }
      if (typeof this.safeStorage.decryptString === 'function') {
        return assertSecret(this.safeStorage.decryptString(encrypted));
      }
    } catch (_error) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.CREDENTIAL_BACKEND_UNAVAILABLE);
    }
    throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.CREDENTIAL_BACKEND_UNAVAILABLE);
  }

  _assertUtilityScope({ utilityInstanceId, sessionToken, provider, operation }) {
    const session = this.utilitySessions.get(utilityInstanceId);
    if (!session || session.sessionToken !== sessionToken) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.UTILITY_AUTH_FAILED);
    }
    if (!session.allowedProviders.includes(provider)) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.PROVIDER_SCOPE_DENIED);
    }
    if (!session.allowedOperations.includes(operation)) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.OPERATION_SCOPE_DENIED);
    }
    return session;
  }

  _activeCredential(credentialId, provider) {
    const credential = this.credentials.get(credentialId);
    if (!credential) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.CREDENTIAL_NOT_FOUND);
    }
    if (credential.status !== CREDENTIAL_STATUS.ACTIVE) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.CREDENTIAL_REVOKED);
    }
    if (credential.provider !== provider) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.CREDENTIAL_PROVIDER_MISMATCH);
    }
    return credential;
  }

  _assertLeaseScope(lease, { utilityInstanceId, provider, operation, correlationId }) {
    if (lease.utilityInstanceId !== utilityInstanceId) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.UTILITY_AUTH_FAILED);
    }
    if (lease.provider !== provider) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.PROVIDER_SCOPE_DENIED);
    }
    if (lease.operation !== operation) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.OPERATION_SCOPE_DENIED);
    }
    if (lease.correlationId !== correlationId) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.INVALID_REQUEST);
    }
  }

  _invalidateCredentialLeases(credentialId, reason) {
    const now = this._nowMs();
    for (const lease of this.leases.values()) {
      if (lease.credentialId === credentialId && !lease.consumedAt && !lease.revokedAt) {
        lease.revokedAt = now;
        lease.revocationReason = reason;
      }
    }
  }

  _nowMs() {
    const value = this.now();
    if (!Number.isFinite(value)) {
      throw new CredentialBrokerError(CREDENTIAL_ERROR_CODES.INVALID_REQUEST, 'clock returned invalid value');
    }
    return Math.trunc(value);
  }
}

module.exports = {
  CREDENTIAL_BROKER_VERSION,
  CREDENTIAL_STATUS,
  CREDENTIAL_ERROR_CODES,
  CredentialBrokerError,
  SafeStorageCredentialBroker,
};
