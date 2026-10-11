'use strict';

const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const {
  CREDENTIAL_ERROR_CODES,
  CredentialBrokerError,
  SafeStorageCredentialBroker,
} = require('../credential-broker.cjs');
const { CHANNELS } = require('../ipc-contract.cjs');
const { createRendererApi } = require('../preload-api.cjs');
const {
  ProductionUtilityBridge,
  UTILITY_CREDENTIAL_MESSAGE_TYPES,
} = require('../production-utility-bridge.cjs');

const CANARY = 'FLOWKIT_CREDENTIAL_CANARY_SUPER_SECRET_2026';

class FakeSafeStorage {
  constructor({ available = true, backend = 'dpapi' } = {}) {
    this.available = available;
    this.backend = backend;
  }

  isEncryptionAvailable() {
    return this.available;
  }

  getSelectedStorageBackend() {
    return this.backend;
  }

  encryptString(secret) {
    const source = Buffer.from(secret, 'utf8');
    const encoded = Buffer.alloc(source.length);
    for (let index = 0; index < source.length; index += 1) {
      encoded[index] = source[index] ^ 0x5a;
    }
    return encoded;
  }

  decryptString(encrypted) {
    const source = Buffer.from(encrypted);
    const decoded = Buffer.alloc(source.length);
    for (let index = 0; index < source.length; index += 1) {
      decoded[index] = source[index] ^ 0x5a;
    }
    return decoded.toString('utf8');
  }
}

async function fixture(options = {}) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'flowkit-credential-broker-'));
  let clock = options.clock ?? 1_800_000_000_000;
  let sequence = 0;
  const broker = new SafeStorageCredentialBroker({
    safeStorage: options.safeStorage || new FakeSafeStorage(),
    vaultPath: path.join(root, 'credential-vault-v1.json'),
    now: () => clock,
    randomUUID: () => `token-${++sequence}`,
    platform: options.platform || 'win32',
    defaultLeaseTtlMs: 1000,
    maxLeaseTtlMs: 5000,
  });
  return {
    broker,
    root,
    vaultPath: path.join(root, 'credential-vault-v1.json'),
    setClock(value) { clock = value; },
    advance(ms) { clock += ms; },
    async close() {
      broker.close();
      await fs.rm(root, { recursive: true, force: true });
    },
  };
}

async function seedCredential(ctx, secret = CANARY) {
  return ctx.broker.putCredential({
    credentialId: 'cred-flow-primary',
    provider: 'FLOW',
    label: 'Production Flow',
    secret,
  });
}

function registerUtility(ctx, overrides = {}) {
  return ctx.broker.registerUtilitySession({
    utilityInstanceId: overrides.utilityInstanceId || 'utility-1',
    sessionToken: overrides.sessionToken || 'session-token-1',
    allowedProviders: overrides.allowedProviders || ['FLOW'],
    allowedOperations: overrides.allowedOperations || ['GENERATE_VIDEO'],
  });
}

async function issueLease(ctx, overrides = {}) {
  return ctx.broker.issueLease({
    utilityInstanceId: overrides.utilityInstanceId || 'utility-1',
    sessionToken: overrides.sessionToken || 'session-token-1',
    credentialId: overrides.credentialId || 'cred-flow-primary',
    provider: overrides.provider || 'FLOW',
    operation: overrides.operation || 'GENERATE_VIDEO',
    correlationId: overrides.correlationId || 'run-001',
    ttlMs: overrides.ttlMs || 1000,
  });
}

async function redeemLease(ctx, lease, overrides = {}) {
  return ctx.broker.redeemLease({
    leaseId: lease.leaseId,
    utilityInstanceId: overrides.utilityInstanceId || 'utility-1',
    sessionToken: overrides.sessionToken || 'session-token-1',
    provider: overrides.provider || 'FLOW',
    operation: overrides.operation || 'GENERATE_VIDEO',
    correlationId: overrides.correlationId || 'run-001',
  });
}

async function expectCode(action, code) {
  await assert.rejects(action, (error) => {
    assert.equal(error instanceof CredentialBrokerError, true);
    assert.equal(error.code, code);
    assert.equal(String(error.message).includes(CANARY), false);
    return true;
  });
}

test('Renderer public API exposes no credential or plaintext-secret capability', async () => {
  const api = createRendererApi({
    invoke: async () => { throw new Error('not used'); },
    randomUUID: () => 'renderer-req-072',
  });
  assert.equal(Object.prototype.hasOwnProperty.call(api, 'credentials'), false);
  assert.equal(Object.prototype.hasOwnProperty.call(api, 'credentialBroker'), false);
  assert.equal(JSON.stringify(Object.keys(api)).includes('secret'), false);
  assert.equal(Object.values(CHANNELS).some((value) => /credential|secret/i.test(value)), false);
});

test('safeStorage vault persists encrypted payload only and metadata never exposes ciphertext or secret', async () => {
  const ctx = await fixture();
  try {
    const metadata = await seedCredential(ctx);
    assert.equal(metadata.credentialVersion, 1);
    assert.equal(metadata.status, 'ACTIVE');
    assert.equal(Object.prototype.hasOwnProperty.call(metadata, 'secret'), false);
    assert.equal(Object.prototype.hasOwnProperty.call(metadata, 'encryptedPayloadB64'), false);

    const vaultText = await fs.readFile(ctx.vaultPath, 'utf8');
    assert.equal(vaultText.includes(CANARY), false);
    assert.equal(vaultText.includes('encryptedPayloadB64'), true);

    const listed = await ctx.broker.listCredentialMetadata();
    assert.equal(JSON.stringify(listed).includes(CANARY), false);
    assert.equal(JSON.stringify(listed).includes('encryptedPayloadB64'), false);
  } finally {
    await ctx.close();
  }
});

test('trusted Utility redeems one scoped lease exactly once and lease metadata contains no secret', async () => {
  const ctx = await fixture();
  try {
    await seedCredential(ctx);
    registerUtility(ctx);
    const lease = await issueLease(ctx);
    assert.equal(Object.prototype.hasOwnProperty.call(lease, 'secret'), false);
    assert.equal(JSON.stringify(lease).includes(CANARY), false);

    const redeemed = await redeemLease(ctx, lease);
    assert.equal(redeemed.secret, CANARY);
    assert.equal(redeemed.lease.credentialVersion, 1);
    assert.equal(redeemed.lease.provider, 'FLOW');
    assert.equal(redeemed.lease.operation, 'GENERATE_VIDEO');

    await expectCode(
      () => redeemLease(ctx, lease),
      CREDENTIAL_ERROR_CODES.LEASE_REPLAY_DENIED
    );
  } finally {
    await ctx.close();
  }
});

test('utility session, provider and operation scope are all fail-closed', async () => {
  const ctx = await fixture();
  try {
    await seedCredential(ctx);
    registerUtility(ctx, {
      allowedProviders: ['FLOW', 'OTHER'],
      allowedOperations: ['GENERATE_VIDEO', 'GENERATE_IMAGE'],
    });

    await expectCode(
      () => issueLease(ctx, { sessionToken: 'wrong-session' }),
      CREDENTIAL_ERROR_CODES.UTILITY_AUTH_FAILED
    );
    await expectCode(
      () => issueLease(ctx, { provider: 'OTHER' }),
      CREDENTIAL_ERROR_CODES.CREDENTIAL_PROVIDER_MISMATCH
    );

    const flowOnlyCtx = await fixture();
    try {
      await seedCredential(flowOnlyCtx);
      registerUtility(flowOnlyCtx);
      await expectCode(
        () => issueLease(flowOnlyCtx, { provider: 'OTHER' }),
        CREDENTIAL_ERROR_CODES.PROVIDER_SCOPE_DENIED
      );
      await expectCode(
        () => issueLease(flowOnlyCtx, { operation: 'GENERATE_IMAGE' }),
        CREDENTIAL_ERROR_CODES.OPERATION_SCOPE_DENIED
      );
    } finally {
      await flowOnlyCtx.close();
    }
  } finally {
    await ctx.close();
  }
});

test('expired lease cannot be redeemed', async () => {
  const ctx = await fixture();
  try {
    await seedCredential(ctx);
    registerUtility(ctx);
    const lease = await issueLease(ctx, { ttlMs: 100 });
    ctx.advance(100);
    await expectCode(
      () => redeemLease(ctx, lease),
      CREDENTIAL_ERROR_CODES.LEASE_EXPIRED
    );
  } finally {
    await ctx.close();
  }
});

test('utility session revocation denies outstanding lease and old session cannot issue a new lease', async () => {
  const ctx = await fixture();
  try {
    await seedCredential(ctx);
    registerUtility(ctx);
    const lease = await issueLease(ctx);
    const revoked = ctx.broker.revokeUtilitySession('utility-1');
    assert.equal(revoked.existed, true);
    assert.equal(revoked.revokedLeaseCount, 1);

    await expectCode(
      () => redeemLease(ctx, lease),
      CREDENTIAL_ERROR_CODES.UTILITY_AUTH_FAILED
    );
    await expectCode(
      () => issueLease(ctx),
      CREDENTIAL_ERROR_CODES.UTILITY_AUTH_FAILED
    );
  } finally {
    await ctx.close();
  }
});

test('credential rotation increments version, invalidates stale lease and new lease sees only new secret', async () => {
  const ctx = await fixture();
  try {
    await seedCredential(ctx, 'old-secret-value');
    registerUtility(ctx);
    const staleLease = await issueLease(ctx, { correlationId: 'run-old' });

    const rotated = await ctx.broker.putCredential({
      credentialId: 'cred-flow-primary',
      provider: 'FLOW',
      label: 'Production Flow',
      secret: 'new-secret-value',
    });
    assert.equal(rotated.credentialVersion, 2);

    await expectCode(
      () => redeemLease(ctx, staleLease, { correlationId: 'run-old' }),
      CREDENTIAL_ERROR_CODES.LEASE_STALE_AFTER_ROTATION
    );

    const freshLease = await issueLease(ctx, { correlationId: 'run-new' });
    const redeemed = await redeemLease(ctx, freshLease, { correlationId: 'run-new' });
    assert.equal(redeemed.secret, 'new-secret-value');
    assert.equal(redeemed.lease.credentialVersion, 2);

    const vaultText = await fs.readFile(ctx.vaultPath, 'utf8');
    assert.equal(vaultText.includes('old-secret-value'), false);
    assert.equal(vaultText.includes('new-secret-value'), false);
  } finally {
    await ctx.close();
  }
});

test('credential revocation blocks new leases and leaves metadata-only revoked record', async () => {
  const ctx = await fixture();
  try {
    await seedCredential(ctx);
    registerUtility(ctx);
    const lease = await issueLease(ctx);
    const metadata = await ctx.broker.revokeCredential({ credentialId: 'cred-flow-primary' });
    assert.equal(metadata.status, 'REVOKED');
    await expectCode(
      () => issueLease(ctx),
      CREDENTIAL_ERROR_CODES.CREDENTIAL_REVOKED
    );
    await expectCode(
      () => redeemLease(ctx, lease),
      CREDENTIAL_ERROR_CODES.LEASE_REVOKED
    );
  } finally {
    await ctx.close();
  }
});

test('unavailable or insecure safeStorage backend fails closed with no plaintext fallback', async () => {
  const unavailable = await fixture({ safeStorage: new FakeSafeStorage({ available: false }) });
  try {
    await expectCode(
      () => seedCredential(unavailable),
      CREDENTIAL_ERROR_CODES.CREDENTIAL_BACKEND_UNAVAILABLE
    );
  } finally {
    await unavailable.close();
  }

  const insecure = await fixture({
    safeStorage: new FakeSafeStorage({ backend: 'basic_text' }),
    platform: 'linux',
  });
  try {
    await expectCode(
      () => seedCredential(insecure),
      CREDENTIAL_ERROR_CODES.CREDENTIAL_INSECURE_BACKEND
    );
  } finally {
    await insecure.close();
  }
});


test('trusted Production Utility receives credentials only through an authorized scoped lease transport', async () => {
  const ctx = await fixture();
  class FakeChild extends EventEmitter {
    constructor() {
      super();
      this.outbound = [];
    }
    postMessage(message) {
      this.outbound.push(message);
    }
    kill() {
      this.emit('exit', 0);
      return true;
    }
  }

  const child = new FakeChild();
  let uuidIndex = 0;
  const bridge = new ProductionUtilityBridge({
    utilityProcess: { fork: () => child },
    entryPath: 'C:/FlowKit/utility-entry.cjs',
    credentialBroker: ctx.broker,
    randomUUID: () => `bridge-${++uuidIndex}`,
  });
  try {
    await seedCredential(ctx);
    const scope = bridge.authorizeCredentialScope({
      allowedProviders: ['FLOW'],
      allowedOperations: ['GENERATE_VIDEO'],
    });
    assert.equal(scope.utilityInstanceId.startsWith('utility-'), true);
    assert.equal(Object.prototype.hasOwnProperty.call(scope, 'sessionToken'), false);

    child.emit('message', {
      type: UTILITY_CREDENTIAL_MESSAGE_TYPES.ISSUE_LEASE,
      requestId: 'lease-req-001',
      credentialId: 'cred-flow-primary',
      provider: 'FLOW',
      operation: 'GENERATE_VIDEO',
      correlationId: 'run-bridge-001',
      ttlMs: 1000,
    });
    await new Promise((resolve) => setImmediate(resolve));
    const leaseResponse = child.outbound.at(-1);
    assert.equal(leaseResponse.type, UTILITY_CREDENTIAL_MESSAGE_TYPES.RESPONSE);
    assert.equal(leaseResponse.ok, true);
    assert.equal(Object.prototype.hasOwnProperty.call(leaseResponse.data, 'secret'), false);
    assert.equal(JSON.stringify(leaseResponse).includes(CANARY), false);
    const lease = leaseResponse.data.lease;

    child.emit('message', {
      type: UTILITY_CREDENTIAL_MESSAGE_TYPES.ISSUE_LEASE,
      requestId: 'lease-req-denied',
      credentialId: 'cred-flow-primary',
      provider: 'FLOW',
      operation: 'GENERATE_IMAGE',
      correlationId: 'run-bridge-denied',
      ttlMs: 1000,
    });
    await new Promise((resolve) => setImmediate(resolve));
    const denied = child.outbound.at(-1);
    assert.equal(denied.ok, false);
    assert.equal(denied.error.code, CREDENTIAL_ERROR_CODES.OPERATION_SCOPE_DENIED);
    assert.equal(JSON.stringify(denied).includes(CANARY), false);

    child.emit('message', {
      type: UTILITY_CREDENTIAL_MESSAGE_TYPES.REDEEM_LEASE,
      requestId: 'lease-redeem-001',
      leaseId: lease.leaseId,
      provider: 'FLOW',
      operation: 'GENERATE_VIDEO',
      correlationId: 'run-bridge-001',
    });
    await new Promise((resolve) => setImmediate(resolve));
    const redeemed = child.outbound.at(-1);
    assert.equal(redeemed.ok, true);
    assert.equal(redeemed.data.secret, CANARY);
    assert.equal(redeemed.data.lease.credentialVersion, 1);

    child.emit('message', {
      type: UTILITY_CREDENTIAL_MESSAGE_TYPES.REDEEM_LEASE,
      requestId: 'lease-replay-001',
      leaseId: lease.leaseId,
      provider: 'FLOW',
      operation: 'GENERATE_VIDEO',
      correlationId: 'run-bridge-001',
    });
    await new Promise((resolve) => setImmediate(resolve));
    const replay = child.outbound.at(-1);
    assert.equal(replay.ok, false);
    assert.equal(replay.error.code, CREDENTIAL_ERROR_CODES.LEASE_REPLAY_DENIED);
    assert.equal(JSON.stringify(replay).includes(CANARY), false);

    bridge.close();
    assert.equal(ctx.broker.utilitySessions.size, 0);
  } finally {
    bridge.close();
    await ctx.close();
  }
});
