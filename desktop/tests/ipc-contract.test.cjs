'use strict';

const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const test = require('node:test');

const {
  CHANNELS,
  IPC_ERROR_CODES,
  IPC_PROTOCOL_VERSION,
  UTILITY_CAPABILITIES,
  assertTrustedRendererSender,
  createBridgeStatusSuccess,
  validateBridgeStatusRequest,
  validateBridgeStatusResponse,
  validateUtilityRequest,
} = require('../ipc-contract.cjs');
const { installProductionIpcHandlers } = require('../ipc-main.cjs');
const { createRendererApi } = require('../preload-api.cjs');
const { ProductionUtilityBridge } = require('../production-utility-bridge.cjs');
const { handleUtilityMessage } = require('../utility-entry.cjs');
const { APP_ORIGIN } = require('../security-policy.cjs');

function trustedSenderFixture() {
  const mainFrame = { url: `${APP_ORIGIN}/index.html` };
  const webContents = { mainFrame };
  const event = { sender: webContents, senderFrame: mainFrame };
  return { event, webContents, mainFrame };
}

function fakeIpcMain() {
  const handlers = new Map();
  return {
    handlers,
    handle(channel, handler) {
      assert.equal(handlers.has(channel), false, `duplicate handler for ${channel}`);
      handlers.set(channel, handler);
    },
    removeHandler(channel) {
      handlers.delete(channel);
    },
  };
}

test('bridge request schema is strict and versioned', () => {
  assert.deepEqual(
    validateBridgeStatusRequest({ apiVersion: IPC_PROTOCOL_VERSION, requestId: 'req-001' }),
    { apiVersion: IPC_PROTOCOL_VERSION, requestId: 'req-001' }
  );
  assert.throws(
    () => validateBridgeStatusRequest({ apiVersion: 999, requestId: 'req-001' }),
    /version mismatch/
  );
  assert.throws(
    () => validateBridgeStatusRequest({ apiVersion: 1, requestId: 'req-001', channel: 'anything' }),
    /unsupported or missing fields/
  );
});

test('utility contract rejects unknown capability and malformed messages', () => {
  assert.deepEqual(
    validateUtilityRequest({
      apiVersion: 1,
      requestId: 'req-002',
      capability: UTILITY_CAPABILITIES.GET_BRIDGE_STATUS,
    }),
    {
      apiVersion: 1,
      requestId: 'req-002',
      capability: UTILITY_CAPABILITIES.GET_BRIDGE_STATUS,
    }
  );
  assert.throws(
    () => validateUtilityRequest({ apiVersion: 1, requestId: 'req-002', capability: 'shell.exec' }),
    /unknown utility capability/
  );
});

test('sender validation requires exact webContents, app origin and main frame', () => {
  const { event, webContents } = trustedSenderFixture();
  assert.equal(assertTrustedRendererSender(event, webContents, APP_ORIGIN), true);

  assert.throws(
    () => assertTrustedRendererSender({ ...event, sender: {} }, webContents, APP_ORIGIN),
    /sender mismatch/
  );
  assert.throws(
    () => assertTrustedRendererSender({ ...event, senderFrame: { url: `${APP_ORIGIN}/iframe` } }, webContents, APP_ORIGIN),
    /frame mismatch/
  );

  const foreignFrame = { url: 'https://example.com/' };
  const foreignWebContents = { mainFrame: foreignFrame };
  assert.throws(
    () => assertTrustedRendererSender(
      { sender: foreignWebContents, senderFrame: foreignFrame },
      foreignWebContents,
      APP_ORIGIN
    ),
    /origin mismatch/
  );
});

test('Main registers only the allowlisted channel and routes a trusted valid request', async () => {
  const ipcMain = fakeIpcMain();
  const { event, webContents } = trustedSenderFixture();
  let calls = 0;
  const bridge = {
    async getBridgeStatus(request) {
      calls += 1;
      return createBridgeStatusSuccess(request.requestId);
    },
  };
  const registration = installProductionIpcHandlers({ ipcMain, webContents, appOrigin: APP_ORIGIN, bridge });

  assert.deepEqual([...ipcMain.handlers.keys()], [CHANNELS.GET_BRIDGE_STATUS]);
  assert.equal(ipcMain.handlers.has('flowkit:generic:invoke'), false);

  const response = await ipcMain.handlers.get(CHANNELS.GET_BRIDGE_STATUS)(event, {
    apiVersion: 1,
    requestId: 'req-003',
  });
  assert.equal(calls, 1);
  assert.equal(validateBridgeStatusResponse(response).ok, true);
  assert.equal(response.data.utilityStatus, 'READY');

  registration.dispose();
  assert.equal(ipcMain.handlers.size, 0);
});

test('invalid schema is denied before Production Utility is called', async () => {
  const ipcMain = fakeIpcMain();
  const { event, webContents } = trustedSenderFixture();
  let calls = 0;
  const bridge = { async getBridgeStatus() { calls += 1; throw new Error('must not run'); } };
  installProductionIpcHandlers({ ipcMain, webContents, appOrigin: APP_ORIGIN, bridge });

  const response = await ipcMain.handlers.get(CHANNELS.GET_BRIDGE_STATUS)(event, {
    apiVersion: 1,
    requestId: 'req-004',
    extra: true,
  });
  assert.equal(calls, 0);
  assert.equal(response.ok, false);
  assert.equal(response.error.code, IPC_ERROR_CODES.INVALID_REQUEST);
  assert.equal(response.error.message, 'Request could not be completed.');
});

test('invalid sender is denied before Production Utility is called', async () => {
  const ipcMain = fakeIpcMain();
  const { event, webContents } = trustedSenderFixture();
  let calls = 0;
  const bridge = { async getBridgeStatus() { calls += 1; throw new Error('must not run'); } };
  installProductionIpcHandlers({ ipcMain, webContents, appOrigin: APP_ORIGIN, bridge });

  const response = await ipcMain.handlers.get(CHANNELS.GET_BRIDGE_STATUS)(
    { ...event, sender: {} },
    { apiVersion: 1, requestId: 'req-005' }
  );
  assert.equal(calls, 0);
  assert.equal(response.ok, false);
  assert.equal(response.error.code, IPC_ERROR_CODES.ACCESS_DENIED);
  assert.equal(response.error.message, 'Request could not be completed.');
});

test('Production Utility bridge performs typed request-response over the child transport', async () => {
  class FakeChild extends EventEmitter {
    postMessage(message) {
      setImmediate(() => this.emit('message', handleUtilityMessage(message)));
    }
    kill() {
      this.emit('exit', 0);
      return true;
    }
  }

  const child = new FakeChild();
  const utilityProcess = { fork(entryPath) { assert.match(entryPath, /utility-entry\.cjs$/); return child; } };
  const bridge = new ProductionUtilityBridge({
    utilityProcess,
    entryPath: 'C:/FlowKit/utility-entry.cjs',
    requestTimeoutMs: 1000,
  });

  const response = await bridge.getBridgeStatus({ apiVersion: 1, requestId: 'req-006' });
  assert.equal(response.ok, true);
  assert.equal(response.requestId, 'req-006');
  assert.deepEqual(response.data.capabilities, [UTILITY_CAPABILITIES.GET_BRIDGE_STATUS]);
  bridge.close();
});

test('Utility returns only redacted error detail for malformed messages', () => {
  const response = handleUtilityMessage({
    apiVersion: 1,
    requestId: 'req-007',
    capability: 'child_process.exec',
  });
  assert.equal(response.ok, false);
  assert.equal(response.error.code, IPC_ERROR_CODES.INVALID_REQUEST);
  assert.equal(response.error.message, 'Request could not be completed.');
  assert.equal('stack' in response.error, false);
});

test('preload API exposes one bounded capability and no generic privileged primitives', async () => {
  const calls = [];
  const api = createRendererApi({
    invoke: async (channel, request) => {
      calls.push({ channel, request });
      return createBridgeStatusSuccess(request.requestId);
    },
    randomUUID: () => 'renderer-req-001',
  });

  assert.deepEqual(Object.keys(api).sort(), [
    'apiVersion',
    'ipcBaseline',
    'productionUtility',
    'securityBaseline',
  ]);
  assert.deepEqual(Object.keys(api.productionUtility), ['getBridgeStatus']);
  for (const forbidden of ['ipcRenderer', 'invoke', 'fs', 'child_process', 'shell', 'exec', 'spawn']) {
    assert.equal(Object.prototype.hasOwnProperty.call(api, forbidden), false);
    assert.equal(Object.prototype.hasOwnProperty.call(api.productionUtility, forbidden), false);
  }

  const response = await api.productionUtility.getBridgeStatus();
  assert.equal(response.ok, true);
  assert.deepEqual(calls, [
    {
      channel: CHANNELS.GET_BRIDGE_STATUS,
      request: { apiVersion: IPC_PROTOCOL_VERSION, requestId: 'renderer-req-001' },
    },
  ]);
});
