'use strict';

const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const test = require('node:test');

const {
  CHANNELS,
  IPC_ERROR_CODES,
  IPC_PROTOCOL_VERSION,
  STUDIO_VIEW_SECTION_KEYS,
  UTILITY_CAPABILITIES,
  assertTrustedRendererSender,
  createBridgeStatusSuccess,
  createStudioApplicationReadModelSuccess,
  validateBridgeStatusRequest,
  validateBridgeStatusResponse,
  validateStudioApplicationReadModelData,
  validateStudioApplicationReadModelRequest,
  validateStudioApplicationReadModelResponse,
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

function studioReadModelFixture(projectId = 'project:film') {
  const sections = {};
  for (const key of STUDIO_VIEW_SECTION_KEYS) {
    sections[key] = {
      status: 'READY',
      items: [
        {
          id: `${key}:001`,
          kind: key,
          label: `${key} view`,
          state: 'READY',
          canonicalRef: {
            logicalId: `view:${projectId}:${key}`,
            versionId: 'v1',
          },
          authority: 'canonical-application',
          provenanceRefs: [`evidence:${key}`],
        },
      ],
    };
  }
  return {
    readModelVersion: 1,
    sourceKind: 'CANONICAL_APPLICATION',
    project: {
      projectId,
      label: 'Film Project',
      workflowState: 'REVIEW',
      activeProfileRef: {
        logicalId: `active-profile:${projectId}`,
        versionId: 'profile-v1',
      },
    },
    sections,
  };
}

function bridgeFixture(overrides = {}) {
  return {
    async getBridgeStatus(request) {
      return createBridgeStatusSuccess(request.requestId);
    },
    async getApplicationReadModel(request) {
      return createStudioApplicationReadModelSuccess(
        request.requestId,
        studioReadModelFixture(request.projectId)
      );
    },
    ...overrides,
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

test('Studio read-model request and response schema are strict and versioned', () => {
  assert.deepEqual(
    validateStudioApplicationReadModelRequest({
      apiVersion: 1,
      requestId: 'req-studio-001',
      projectId: 'project:film',
    }),
    { apiVersion: 1, requestId: 'req-studio-001', projectId: 'project:film' }
  );
  assert.throws(
    () => validateStudioApplicationReadModelRequest({
      apiVersion: 1,
      requestId: 'req-studio-001',
      projectId: 'project:film',
      providerPayload: {},
    }),
    /unsupported or missing fields/
  );

  const model = validateStudioApplicationReadModelData(studioReadModelFixture());
  assert.equal(model.sourceKind, 'CANONICAL_APPLICATION');
  assert.deepEqual(Object.keys(model.sections).sort(), [...STUDIO_VIEW_SECTION_KEYS].sort());

  const missingSection = studioReadModelFixture();
  delete missingSection.sections.evidenceStatus;
  assert.throws(() => validateStudioApplicationReadModelData(missingSection), /unsupported or missing fields/);

  const leakedProviderPayload = { ...studioReadModelFixture(), provider: { token: 'forbidden' } };
  assert.throws(
    () => validateStudioApplicationReadModelData(leakedProviderPayload),
    /unsupported or missing fields/
  );
});

test('Studio read-model response is bound to the requested project', () => {
  const wrongProject = createStudioApplicationReadModelSuccess(
    'req-project-binding',
    studioReadModelFixture('project:other')
  );
  assert.throws(
    () => validateStudioApplicationReadModelResponse(wrongProject, 'project:film'),
    /project binding mismatch/
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
  assert.deepEqual(
    validateUtilityRequest({
      apiVersion: 1,
      requestId: 'req-studio-002',
      capability: UTILITY_CAPABILITIES.GET_STUDIO_APPLICATION_READ_MODEL,
      projectId: 'project:film',
    }),
    {
      apiVersion: 1,
      requestId: 'req-studio-002',
      capability: UTILITY_CAPABILITIES.GET_STUDIO_APPLICATION_READ_MODEL,
      projectId: 'project:film',
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

test('Main registers only the two allowlisted capabilities and routes trusted valid requests', async () => {
  const ipcMain = fakeIpcMain();
  const { event, webContents } = trustedSenderFixture();
  let statusCalls = 0;
  let studioCalls = 0;
  const bridge = bridgeFixture({
    async getBridgeStatus(request) {
      statusCalls += 1;
      return createBridgeStatusSuccess(request.requestId);
    },
    async getApplicationReadModel(request) {
      studioCalls += 1;
      return createStudioApplicationReadModelSuccess(
        request.requestId,
        studioReadModelFixture(request.projectId)
      );
    },
  });
  const registration = installProductionIpcHandlers({ ipcMain, webContents, appOrigin: APP_ORIGIN, bridge });

  assert.deepEqual([...ipcMain.handlers.keys()].sort(), Object.values(CHANNELS).sort());
  assert.equal(ipcMain.handlers.has('flowkit:generic:invoke'), false);

  const status = await ipcMain.handlers.get(CHANNELS.GET_BRIDGE_STATUS)(event, {
    apiVersion: 1,
    requestId: 'req-003',
  });
  assert.equal(statusCalls, 1);
  assert.equal(validateBridgeStatusResponse(status).ok, true);

  const studio = await ipcMain.handlers.get(CHANNELS.GET_STUDIO_APPLICATION_READ_MODEL)(event, {
    apiVersion: 1,
    requestId: 'req-studio-003',
    projectId: 'project:film',
  });
  assert.equal(studioCalls, 1);
  assert.equal(validateStudioApplicationReadModelResponse(studio).ok, true);
  assert.equal(studio.data.project.projectId, 'project:film');

  registration.dispose();
  assert.equal(ipcMain.handlers.size, 0);
});

test('invalid Studio schema is denied before Production Utility is called', async () => {
  const ipcMain = fakeIpcMain();
  const { event, webContents } = trustedSenderFixture();
  let calls = 0;
  const bridge = bridgeFixture({
    async getApplicationReadModel() {
      calls += 1;
      throw new Error('must not run');
    },
  });
  installProductionIpcHandlers({ ipcMain, webContents, appOrigin: APP_ORIGIN, bridge });

  const response = await ipcMain.handlers.get(CHANNELS.GET_STUDIO_APPLICATION_READ_MODEL)(event, {
    apiVersion: 1,
    requestId: 'req-004',
    projectId: 'project:film',
    extra: true,
  });
  assert.equal(calls, 0);
  assert.equal(response.ok, false);
  assert.equal(response.error.code, IPC_ERROR_CODES.INVALID_REQUEST);
  assert.equal(response.error.message, 'Request could not be completed.');
});

test('invalid sender is denied before Studio Production Utility capability is called', async () => {
  const ipcMain = fakeIpcMain();
  const { event, webContents } = trustedSenderFixture();
  let calls = 0;
  const bridge = bridgeFixture({
    async getApplicationReadModel() {
      calls += 1;
      throw new Error('must not run');
    },
  });
  installProductionIpcHandlers({ ipcMain, webContents, appOrigin: APP_ORIGIN, bridge });

  const response = await ipcMain.handlers.get(CHANNELS.GET_STUDIO_APPLICATION_READ_MODEL)(
    { ...event, sender: {} },
    { apiVersion: 1, requestId: 'req-005', projectId: 'project:film' }
  );
  assert.equal(calls, 0);
  assert.equal(response.ok, false);
  assert.equal(response.error.code, IPC_ERROR_CODES.ACCESS_DENIED);
  assert.equal(response.error.message, 'Request could not be completed.');
});

test('Production Utility bridge performs typed status request-response over child transport', async () => {
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
  assert.deepEqual([...response.data.capabilities].sort(), Object.values(UTILITY_CAPABILITIES).sort());
  bridge.close();
});

test('Production Utility Studio read model fails closed without canonical application provider', async () => {
  const response = await handleUtilityMessage({
    apiVersion: 1,
    requestId: 'req-studio-unavailable',
    capability: UTILITY_CAPABILITIES.GET_STUDIO_APPLICATION_READ_MODEL,
    projectId: 'project:film',
  });
  assert.equal(response.ok, false);
  assert.equal(response.error.code, IPC_ERROR_CODES.APPLICATION_READ_MODEL_UNAVAILABLE);
  assert.equal(response.error.message, 'Request could not be completed.');
  assert.equal('stack' in response.error, false);
});

test('Production Utility accepts injected canonical application provider and bridge validates its output', async () => {
  const provider = ({ projectId }) => studioReadModelFixture(projectId);
  class FakeChild extends EventEmitter {
    postMessage(message) {
      Promise.resolve(handleUtilityMessage(message, { applicationReadModelProvider: provider }))
        .then((response) => setImmediate(() => this.emit('message', response)));
    }
    kill() {
      this.emit('exit', 0);
      return true;
    }
  }

  const child = new FakeChild();
  const bridge = new ProductionUtilityBridge({
    utilityProcess: { fork: () => child },
    entryPath: 'C:/FlowKit/utility-entry.cjs',
    requestTimeoutMs: 1000,
  });
  const response = await bridge.getApplicationReadModel({
    apiVersion: 1,
    requestId: 'req-studio-bridge',
    projectId: 'project:film',
  });
  assert.equal(response.ok, true);
  assert.equal(response.data.sourceKind, 'CANONICAL_APPLICATION');
  assert.deepEqual(Object.keys(response.data.sections).sort(), [...STUDIO_VIEW_SECTION_KEYS].sort());
  bridge.close();
});

test('Production Utility bridge rejects a canonical read model bound to a different project', async () => {
  const provider = () => studioReadModelFixture('project:other');
  class FakeChild extends EventEmitter {
    postMessage(message) {
      Promise.resolve(handleUtilityMessage(message, { applicationReadModelProvider: provider }))
        .then((response) => setImmediate(() => this.emit('message', response)));
    }
    kill() {
      this.emit('exit', 0);
      return true;
    }
  }

  const bridge = new ProductionUtilityBridge({
    utilityProcess: { fork: () => new FakeChild() },
    entryPath: 'C:/FlowKit/utility-entry.cjs',
    requestTimeoutMs: 1000,
  });
  await assert.rejects(
    () => bridge.getApplicationReadModel({
      apiVersion: 1,
      requestId: 'req-studio-wrong-project',
      projectId: 'project:film',
    }),
    /project binding mismatch/
  );
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

test('preload API exposes bounded status + Studio read-model capabilities and no generic primitives', async () => {
  const calls = [];
  let uuidIndex = 0;
  const api = createRendererApi({
    invoke: async (channel, request) => {
      calls.push({ channel, request });
      if (channel === CHANNELS.GET_BRIDGE_STATUS) {
        return createBridgeStatusSuccess(request.requestId);
      }
      return createStudioApplicationReadModelSuccess(
        request.requestId,
        studioReadModelFixture(request.projectId)
      );
    },
    randomUUID: () => `renderer-req-${++uuidIndex}`,
  });

  assert.deepEqual(Object.keys(api).sort(), [
    'apiVersion',
    'ipcBaseline',
    'productionUtility',
    'securityBaseline',
    'studio',
  ]);
  assert.deepEqual(Object.keys(api.productionUtility), ['getBridgeStatus']);
  assert.deepEqual(Object.keys(api.studio), ['getApplicationReadModel']);
  for (const forbidden of ['ipcRenderer', 'invoke', 'fs', 'child_process', 'shell', 'exec', 'spawn', 'credentials', 'secret']) {
    assert.equal(Object.prototype.hasOwnProperty.call(api, forbidden), false);
    assert.equal(Object.prototype.hasOwnProperty.call(api.productionUtility, forbidden), false);
    assert.equal(Object.prototype.hasOwnProperty.call(api.studio, forbidden), false);
  }

  const statusResponse = await api.productionUtility.getBridgeStatus();
  assert.equal(statusResponse.ok, true);
  const studioResponse = await api.studio.getApplicationReadModel('project:film');
  assert.equal(studioResponse.ok, true);
  assert.equal(studioResponse.data.project.projectId, 'project:film');
  assert.deepEqual(calls, [
    {
      channel: CHANNELS.GET_BRIDGE_STATUS,
      request: { apiVersion: IPC_PROTOCOL_VERSION, requestId: 'renderer-req-1' },
    },
    {
      channel: CHANNELS.GET_STUDIO_APPLICATION_READ_MODEL,
      request: {
        apiVersion: IPC_PROTOCOL_VERSION,
        requestId: 'renderer-req-2',
        projectId: 'project:film',
      },
    },
  ]);
});
