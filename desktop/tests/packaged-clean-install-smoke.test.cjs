'use strict';

const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const test = require('node:test');
const crypto = require('node:crypto');
const { extractFile } = require('@electron/asar');

const configuredPackageDir = process.env.FLOWKIT_PACKAGED_APP_DIR;
const smokeEnabled = Boolean(configuredPackageDir);
const packageDir = path.resolve(configuredPackageDir || '.');
const executable = path.join(packageDir, 'FlowKit Studio.exe');
const asarPath = path.join(packageDir, 'resources', 'app.asar');
const artifactRoot = path.resolve(
  process.env.FLOWKIT_SECURITY_ARTIFACT_DIR || path.resolve(packageDir, '..')
);
const repositoryRoot = path.resolve(__dirname, '..', '..');

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function exists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function inventory(root) {
  let files = 0;
  let bytes = 0;
  async function visit(directory) {
    for (const entry of await fs.readdir(directory, { withFileTypes: true })) {
      const fullPath = path.join(directory, entry.name);
      if (entry.isDirectory()) {
        await visit(fullPath);
      } else if (entry.isFile()) {
        const stat = await fs.stat(fullPath);
        files += 1;
        bytes += stat.size;
      }
    }
  }
  await visit(root);
  return { files, bytes };
}

async function findFilesNamed(root, fileName) {
  const matches = [];
  async function visit(directory) {
    for (const entry of await fs.readdir(directory, { withFileTypes: true })) {
      const fullPath = path.join(directory, entry.name);
      if (entry.isDirectory()) {
        await visit(fullPath);
      } else if (entry.isFile() && entry.name === fileName) {
        matches.push(fullPath);
      }
    }
  }
  await visit(root);
  return matches.sort();
}

async function waitFor(readiness, options = {}) {
  const timeoutMs = options.timeoutMs || 30000;
  const label = options.label || 'readiness';
  const child = options.child || null;
  const deadline = Date.now() + timeoutMs;
  let lastError = null;
  while (Date.now() < deadline) {
    if (child && child.exitCode !== null) {
      throw new Error(label + ': packaged app exited early with code ' + child.exitCode);
    }
    try {
      const result = await readiness();
      if (result !== null && result !== undefined && result !== false) return result;
    } catch (error) {
      lastError = error;
    }
    await sleep(150);
  }
  throw new Error(label + ': readiness timeout' + (lastError ? ' (' + lastError.message + ')' : ''));
}

function createCdpClient(url) {
  if (typeof WebSocket !== 'function') {
    throw new Error('Node WebSocket API is unavailable; Node 22+ is required');
  }
  const socket = new WebSocket(url);
  let nextId = 0;
  const pending = new Map();
  const events = [];
  let openedResolve;
  let openedReject;
  const opened = new Promise((resolve, reject) => {
    openedResolve = resolve;
    openedReject = reject;
  });

  socket.addEventListener('open', () => openedResolve());
  socket.addEventListener('error', () => openedReject(new Error('CDP WebSocket connection failed')));
  socket.addEventListener('message', async (event) => {
    try {
      const raw = typeof event.data === 'string' ? event.data : await event.data.text();
      const message = JSON.parse(raw);
      if (!message.id) { events.push(message); return; }
      if (!pending.has(message.id)) return;
      const item = pending.get(message.id);
      pending.delete(message.id);
      clearTimeout(item.timer);
      if (message.error) {
        item.reject(new Error('CDP ' + item.method + ': ' + (message.error.message || 'command failed')));
      } else {
        item.resolve(message.result || {});
      }
    } catch (error) {
      for (const item of pending.values()) {
        clearTimeout(item.timer);
        item.reject(error);
      }
      pending.clear();
    }
  });
  socket.addEventListener('close', () => {
    for (const item of pending.values()) {
      clearTimeout(item.timer);
      item.reject(new Error('CDP socket closed'));
    }
    pending.clear();
  });

  return {
    async ready() {
      await Promise.race([
        opened,
        sleep(5000).then(() => { throw new Error('CDP WebSocket open timeout'); }),
      ]);
    },
    send(method, params = {}) {
      const id = ++nextId;
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
          pending.delete(id);
          reject(new Error('CDP command timeout: ' + method));
        }, 10000);
        pending.set(id, { resolve, reject, timer, method });
        socket.send(JSON.stringify({ id, method, params }));
      });
    },
    events,
    close() {
      try { socket.close(); } catch {}
    },
  };
}

async function terminateChild(child) {
  if (child.exitCode !== null) return;
  const exited = new Promise((resolve) => child.once('exit', resolve));
  try { child.kill(); } catch {}
  await Promise.race([exited, sleep(3000)]);
}

async function closeGracefully(child, cdp) {
  if (child.exitCode !== null) return child.exitCode;
  try {
    await cdp.send('Page.close');
  } catch {
    // Closing the last Electron window may close the CDP socket before its response.
  }
  return waitFor(
    async () => child.exitCode !== null ? child.exitCode : null,
    { timeoutMs: 15000, label: 'graceful app shutdown' }
  );
}

async function launchAndProbe(runName, userDataDir) {
  await fs.mkdir(userDataDir, { recursive: true });
  const appDataRoot = path.join(userDataDir, 'isolated-appdata');
  const localAppDataRoot = path.join(userDataDir, 'isolated-localappdata');
  const tempRoot = path.join(userDataDir, 'isolated-temp');
  await Promise.all([
    fs.mkdir(appDataRoot, { recursive: true }),
    fs.mkdir(localAppDataRoot, { recursive: true }),
    fs.mkdir(tempRoot, { recursive: true }),
  ]);
  const activePortFile = path.join(userDataDir, 'DevToolsActivePort');
  await fs.rm(activePortFile, { force: true });

  const stdoutPath = path.join(artifactRoot, runName + '.stdout.log');
  const stderrPath = path.join(artifactRoot, runName + '.stderr.log');
  const stdout = await fs.open(stdoutPath, 'w');
  const stderr = await fs.open(stderrPath, 'w');
  const child = spawn(
    executable,
    [
      '--user-data-dir=' + userDataDir,
      '--remote-debugging-port=0',
      '--no-first-run',
      '--no-default-browser-check',
    ],
    {
      cwd: packageDir,
      windowsHide: false,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: {
        ...process.env,
        APPDATA: appDataRoot,
        LOCALAPPDATA: localAppDataRoot,
        TEMP: tempRoot,
        TMP: tempRoot,
      },
    }
  );
  child.stdout.on('data', (chunk) => { void stdout.write(chunk).catch(() => {}); });
  child.stderr.on('data', (chunk) => { void stderr.write(chunk).catch(() => {}); });
  child.on('error', (error) => { void stderr.write('CHILD_SPAWN_ERROR=' + String(error && error.stack || error) + '\\n'); });
  child.on('exit', (code, signal) => { void stderr.write('CHILD_EXIT code=' + code + ' signal=' + signal + '\\n'); });
  void stderr.write('CHILD_STARTED pid=' + child.pid + ' executable=' + executable + ' cwd=' + packageDir + ' userDataDir=' + userDataDir + '\\n');
  let cdp = null;

  try {
    const portText = await waitFor(async () => {
      if (!(await exists(activePortFile))) return null;
      const text = (await fs.readFile(activePortFile, 'utf8')).split(/\r?\n/)[0].trim();
      return /^\d+$/.test(text) ? text : null;
    }, { timeoutMs: 30000, label: runName + ' DevToolsActivePort', child });

    const port = Number(portText);
    const target = await waitFor(async () => {
      const response = await fetch('http://127.0.0.1:' + port + '/json/list', {
        signal: AbortSignal.timeout(1500),
      });
      if (!response.ok) return null;
      const items = await response.json();
      return items.find((item) => item.type === 'page' && item.webSocketDebuggerUrl && item.url.startsWith('flowkit://app/')) || null;
    }, { timeoutMs: 30000, label: runName + ' renderer target', child });

    cdp = createCdpClient(target.webSocketDebuggerUrl);
    await cdp.ready();
    await cdp.send('Runtime.enable');
    const contexts = cdp.events
      .filter((event) => event.method === 'Runtime.executionContextCreated')
      .map((event) => ({ id: event.params.context.id, name: event.params.context.name, auxData: event.params.context.auxData }));
    const defaultContext = contexts.find((context) => context.auxData && context.auxData.isDefault === true);
    const expression = [
      '(async () => {',
      "  const waitForLoad = () => document.readyState === 'complete' ? Promise.resolve() : new Promise((resolve) => window.addEventListener('load', resolve, { once: true }));",
      '  await waitForLoad();',
      '  const host = window.flowkitHost;',
      "  if (!host) return { preloadPresent: false, location: location.href, title: document.title, readyState: document.readyState, hasRequire: typeof require };",
      '  const apiKeys = Object.keys(host).sort();',
      '  const bridge = await host.productionUtility.getBridgeStatus();',
      '  let readModel = null;',
      "  try { readModel = await host.studio.getApplicationReadModel('imp105-clean-install-smoke'); }",
      "  catch (error) { readModel = { thrown: true, message: String(error && error.message || 'unknown') }; }",
      '  await new Promise((resolve) => setTimeout(resolve, 100));',
      '  return {',
      '    preloadPresent: true,',
      '    location: location.href,',
      '    title: document.title,',
      '    readyState: document.readyState,',
      "    appHeading: document.querySelector('h1')?.textContent || '',",
      '    bridge,',
      "    bridgeBadge: document.querySelector('#bridge-status')?.textContent || '',",
      "    bridgeState: document.querySelector('#bridge-status')?.dataset.state || '',",
      '    readModel,',
      "    hasProjectForm: Boolean(document.querySelector('#project-form')),",
      '    apiKeys,',
      '  };',
      '})()',
    ].join('\n');
    const evaluation = await cdp.send('Runtime.evaluate', {
      expression,
      awaitPromise: true,
      returnByValue: true,
    });

    if (evaluation.exceptionDetails) {
      throw new Error('Renderer health probe failed: ' + (evaluation.exceptionDetails.text || 'evaluation exception'));
    }
    const result = evaluation.result && evaluation.result.value;
    assert.ok(result && typeof result === 'object', 'renderer probe must return a structured result');
    assert.equal(result.preloadPresent, true, 'preload API missing; target=' + target.url + '; contexts=' + JSON.stringify(contexts));
    assert.equal(result.title, 'FlowKit Studio');
    assert.equal(result.appHeading, 'FlowKit Studio');
    assert.equal(result.readyState, 'complete');
    assert.equal(result.hasProjectForm, true);
    assert.deepEqual(result.apiKeys, ['apiVersion', 'ipcBaseline', 'productionUtility', 'securityBaseline', 'studio']);
    assert.equal(result.bridge && result.bridge.ok, true, 'renderer -> IPC -> Utility bridge must be healthy');
    assert.equal(result.bridgeState, 'ready');
    assert.match(result.bridgeBadge, /Utility READY/);
    assert.equal(result.readModel && result.readModel.ok, false, 'absent read-model provider must fail closed');
    assert.equal(result.readModel.error && result.readModel.error.code, 'APPLICATION_READ_MODEL_UNAVAILABLE');

    assert.equal(await exists(activePortFile), true, 'fresh isolated Chromium profile must be initialized');
    const credentialVaultFiles = await findFilesNamed(userDataDir, 'credential-vault-v1.json');
    assert.deepEqual(credentialVaultFiles, [], 'clean install must not create a credential vault anywhere in isolated app data');

    const exitCode = await closeGracefully(child, cdp);
    return {
      runName,
      pid: child.pid,
      exitCode,
      userDataDir,
      logFiles: [stdoutPath, stderrPath],
      renderer: {
        title: result.title,
        readyState: result.readyState,
        hasProjectForm: result.hasProjectForm,
        apiKeys: result.apiKeys,
      },
      utilityIpc: {
        ok: result.bridge.ok,
        badge: result.bridgeBadge,
        state: result.bridgeState,
      },
      readModel: {
        ok: result.readModel.ok,
        errorCode: result.readModel.error.code,
      },
      devToolsActivePortPresent: await exists(activePortFile),
      credentialVaultPresent: (await findFilesNamed(userDataDir, 'credential-vault-v1.json')).length > 0,
    };
  } catch (error) {
    await terminateChild(child);
    throw error;
  } finally {
    cdp?.close();
    await stdout.close().catch(() => {});
    await stderr.close().catch(() => {});
  }
}

test(
  'fresh-copy packaged Windows app completes first-run and restart with renderer/IPC/Utility health',
  { skip: !smokeEnabled || process.platform !== 'win32', timeout: 120000 },
  async () => {
    assert.equal(await exists(executable), true, 'fresh-copy executable must exist');
    assert.equal(await exists(asarPath), true, 'fresh-copy app.asar must exist');
    assert.equal(await exists(path.join(packageDir, 'resources', 'app')), false, 'packaged app must not depend on unpackaged source');
    assert.equal(await exists(path.join(packageDir, 'node_modules')), false, 'packaged app must not depend on development node_modules');

    const sourceDesktop = path.resolve(repositoryRoot, 'desktop');
    const relativeFromDesktop = path.relative(sourceDesktop, packageDir);
    assert.ok(
      relativeFromDesktop.startsWith('..') && !path.isAbsolute(relativeFromDesktop),
      'smoke must launch a copied package outside the desktop source tree'
    );

    const packageHash = crypto.createHash('sha256').update(await fs.readFile(asarPath)).digest('hex');
    const sourcePackageDir = path.join(artifactRoot, 'package', 'win-unpacked');
    const sourceAsar = path.join(sourcePackageDir, 'resources', 'app.asar');
    const sourceHash = crypto.createHash('sha256').update(await fs.readFile(sourceAsar)).digest('hex');
    assert.equal(packageHash, sourceHash, 'fresh copy must match the retained packaged artifact byte-for-byte');
    const packageInventory = await inventory(packageDir);
    const sourceInventory = await inventory(sourcePackageDir);
    assert.deepEqual(packageInventory, sourceInventory, 'fresh-copy file inventory must match the retained package');

    const userDataDir = path.join(artifactRoot, 'runtime-user-data');
    await fs.rm(userDataDir, { recursive: true, force: true });
    await fs.mkdir(userDataDir, { recursive: true });
    const firstRun = await launchAndProbe('first-run', userDataDir);
    assert.equal(firstRun.exitCode, 0, 'first-run app must exit cleanly after the health probe');
    assert.equal(firstRun.credentialVaultPresent, false);

    const restart = await launchAndProbe('restart', userDataDir);
    assert.equal(restart.exitCode, 0, 'restart app must exit cleanly after the health probe');
    assert.equal(restart.credentialVaultPresent, false);

    const result = {
      schemaVersion: 1,
      marker: 'FLOWKIT_IMP105_PACKAGED_CLEAN_INSTALL_SMOKE',
      status: 'PASS',
      packageDir,
      packageAsarSha256: packageHash,
      sourcePackageAsarSha256: sourceHash,
      packageFileInventory: packageInventory.files,
      packageByteInventory: packageInventory.bytes,
      firstRun,
      restart,
      schemaGate: 'covered-by-packaged-credential-vault-negative-case',
    };
    await fs.writeFile(
      path.join(artifactRoot, 'clean-install-smoke-result.json'),
      JSON.stringify(result, null, 2) + '\n',
      'utf8'
    );
  }
);

test(
  'packaged credential vault schema gate rejects unsupported schema without rewriting the vault',
  { skip: !smokeEnabled, timeout: 15000 },
  async () => {
    assert.equal(await exists(asarPath), true);
    const extractionRoot = await fs.mkdtemp(path.join(os.tmpdir(), 'flowkit-imp105-schema-'));
    try {
      const brokerSource = extractFile(asarPath, 'credential-broker.cjs');
      const brokerPath = path.join(extractionRoot, 'credential-broker.cjs');
      await fs.writeFile(brokerPath, brokerSource);

      const { CREDENTIAL_ERROR_CODES, SafeStorageCredentialBroker } = require(brokerPath);
      const vaultPath = path.join(extractionRoot, 'credential-vault-v1.json');
      const unsupportedVault = JSON.stringify({ schemaVersion: 999, credentials: [] }, null, 2) + '\n';
      await fs.writeFile(vaultPath, unsupportedVault, 'utf8');

      const broker = new SafeStorageCredentialBroker({
        safeStorage: { isEncryptionAvailable: () => true },
        vaultPath,
        platform: 'win32',
      });
      try {
        await assert.rejects(
          broker.listCredentialMetadata(),
          (error) => error && error.code === CREDENTIAL_ERROR_CODES.VAULT_CORRUPT
        );
        assert.equal(await fs.readFile(vaultPath, 'utf8'), unsupportedVault);
      } finally {
        broker.close();
      }
    } finally {
      await fs.rm(extractionRoot, { recursive: true, force: true });
    }
  }
);
