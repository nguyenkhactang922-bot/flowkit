'use strict';

const assert = require('node:assert/strict');
const { spawn, spawnSync } = require('node:child_process');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { extractFile, listPackage } = require('@electron/asar');

const configuredPackageDir = process.env.FLOWKIT_PACKAGED_APP_DIR;
const packageTestsEnabled = Boolean(configuredPackageDir);

function packagePaths() {
  const packageDir = path.resolve(configuredPackageDir || '.');
  return {
    packageDir,
    executable: path.join(packageDir, 'FlowKit Studio.exe'),
    asarPath: path.join(packageDir, 'resources', 'app.asar'),
  };
}

function extractText(asarPath, relativePath) {
  return extractFile(asarPath, relativePath).toString('utf8');
}

async function extractModule(asarPath, extractionRoot, relativePath) {
  const destination = path.join(extractionRoot, relativePath);
  await fs.mkdir(path.dirname(destination), { recursive: true });
  await fs.writeFile(destination, extractFile(asarPath, relativePath));
  return destination;
}

async function exists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

test(
  'packaged ASAR keeps the narrow security boundary and rejects negative cases',
  { skip: !packageTestsEnabled },
  async (t) => {
    const { packageDir, executable, asarPath } = packagePaths();
    assert.equal(await exists(executable), true, 'packaged Windows executable must exist');
    assert.equal(await exists(asarPath), true, 'packaged ASAR must exist');

    const entries = listPackage(asarPath).map((entry) => {
      const normalized = entry.split(String.fromCharCode(92)).join('/');
      return normalized.startsWith('/') ? normalized.slice(1) : normalized;
    });
    const requiredEntries = [
      'main.cjs',
      'preload.cjs',
      'preload-api.cjs',
      'security-policy.cjs',
      'credential-broker.cjs',
      'ipc-contract.cjs',
      'ipc-main.cjs',
      'production-utility-bridge.cjs',
      'utility-entry.cjs',
      'renderer/index.html',
      'renderer/app.js',
      'renderer/styles.css',
    ];
    for (const entry of requiredEntries) {
      assert.ok(entries.includes(entry), 'missing packaged security file: ' + entry);
    }
    const forbiddenEntries = entries.filter((entry) => {
      const segments = entry.split('/').filter(Boolean).map((segment) => segment.toLowerCase());
      return (
        segments.includes('tests') ||
        segments.includes('node_modules') ||
        segments.some((segment) => segment === '.env' || segment.startsWith('.env.')) ||
        entry.toLowerCase().endsWith('credential-vault-v1.json') ||
        /\.(pem|pfx|p12|key)$/i.test(entry)
      );
    });
    assert.deepEqual(
      forbiddenEntries,
      [],
      'tests, dependencies, vault data and signing keys must not ship in app.asar'
    );

    const packageMetadata = JSON.parse(extractText(asarPath, 'package.json'));
    assert.equal(packageMetadata.version, '0.1.0');
    assert.equal(packageMetadata.productName, 'FlowKit Studio');
    assert.equal(packageMetadata.main, 'main.cjs');
    assert.equal(await exists(path.join(packageDir, 'resources', 'app')), false, 'app source must be packed into app.asar');

    const mainSource = extractText(asarPath, 'main.cjs');
    for (const setting of [
      /nodeIntegration:\s*false/,
      /contextIsolation:\s*true/,
      /sandbox:\s*true/,
      /webSecurity:\s*true/,
      /allowRunningInsecureContent:\s*false/,
      /experimentalFeatures:\s*false/,
      /webviewTag:\s*false/,
      /navigateOnDragDrop:\s*false/,
    ]) {
      assert.match(mainSource, setting, 'packaged BrowserWindow setting missing: ' + setting);
    }
    assert.match(mainSource, /--flowkit-security-self-test/);
    assert.doesNotMatch(mainSource, /--remote-debugging-port/);

    const preloadSource = extractText(asarPath, 'preload.cjs');
    assert.match(
      preloadSource,
      /contextBridge\.exposeInMainWorld\(['"]flowkitHost['"],\s*rendererApi\)/
    );
    assert.doesNotMatch(
      preloadSource,
      /exposeInMainWorld\(['"](?:ipcRenderer|safeStorage|credentialBroker|process|require)['"]/
    );

    const rendererHtml = extractText(asarPath, 'renderer/index.html');
    for (const directive of [
      "default-src 'self'",
      "script-src 'self'",
      "connect-src 'self'",
      "object-src 'none'",
      "base-uri 'none'",
      "frame-ancestors 'none'",
    ]) {
      assert.ok(rendererHtml.includes(directive), 'packaged CSP missing directive: ' + directive);
    }

    const extractionRoot = await fs.mkdtemp(path.join(os.tmpdir(), 'flowkit-imp104-asar-'));
    t.after(async () => fs.rm(extractionRoot, { recursive: true, force: true }));
    await Promise.all(
      ['security-policy.cjs', 'ipc-contract.cjs', 'preload-api.cjs', 'ipc-main.cjs'].map((file) =>
        extractModule(asarPath, extractionRoot, file)
      )
    );

    const policy = require(path.join(extractionRoot, 'security-policy.cjs'));
    const contract = require(path.join(extractionRoot, 'ipc-contract.cjs'));
    const createRendererApi = require(path.join(extractionRoot, 'preload-api.cjs')).createRendererApi;
    const installProductionIpcHandlers =
      require(path.join(extractionRoot, 'ipc-main.cjs')).installProductionIpcHandlers;

    assert.equal(policy.isAllowedAppUrl(policy.APP_ORIGIN + '/index.html'), true);
    for (const url of [
      'https://127.0.0.1:1/blocked',
      'file:///C:/Windows/win.ini',
      'javascript:alert(1)',
      'data:text/html,blocked',
      'not a URL',
    ]) {
      assert.equal(policy.isAllowedAppUrl(url), false, 'foreign URL unexpectedly accepted: ' + url);
    }
    const rendererRoot = path.join(extractionRoot, 'renderer');
    await fs.mkdir(rendererRoot, { recursive: true });
    await fs.writeFile(path.join(rendererRoot, 'index.html'), rendererHtml);
    assert.equal(
      policy.resolveRendererPath(rendererRoot, policy.APP_ORIGIN + '/index.html'),
      path.join(rendererRoot, 'index.html')
    );
    assert.equal(
      policy.resolveRendererPath(rendererRoot, policy.APP_ORIGIN + '/%2e%2e%2fsecret.txt'),
      null
    );

    const navigationHandlers = new Map();
    let windowOpenHandler;
    const guardedWebContents = {
      on(name, handler) {
        navigationHandlers.set(name, handler);
      },
      setWindowOpenHandler(handler) {
        windowOpenHandler = handler;
      },
    };
    policy.installNavigationGuards(guardedWebContents);
    let navigationPrevented = false;
    navigationHandlers.get('will-navigate')(
      { preventDefault() { navigationPrevented = true; } },
      'https://127.0.0.1:1/blocked'
    );
    assert.equal(navigationPrevented, true);
    assert.deepEqual(windowOpenHandler({ url: 'https://127.0.0.1:1/blocked' }), { action: 'deny' });
    assert.deepEqual(windowOpenHandler({ url: policy.APP_ORIGIN + '/popup' }), { action: 'deny' });
    let webviewPrevented = false;
    navigationHandlers.get('will-attach-webview')({
      preventDefault() { webviewPrevented = true; },
    });
    assert.equal(webviewPrevented, true);

    const unknownCapability = {
      apiVersion: 1,
      requestId: 'req-imp104-unknown',
      capability: 'credential.read-secret',
    };
    assert.throws(
      () => contract.validateUtilityRequest(unknownCapability),
      { code: contract.IPC_ERROR_CODES.INVALID_REQUEST }
    );
    assert.throws(
      () => contract.validateUtilityRequest({
        apiVersion: 1,
        requestId: 'req-imp104-extra',
        capability: contract.UTILITY_CAPABILITIES.GET_BRIDGE_STATUS,
        secret: 'SYNTHETIC_TEST_VALUE',
      }),
      { code: contract.IPC_ERROR_CODES.INVALID_REQUEST }
    );

    const mainFrame = { url: policy.APP_ORIGIN + '/index.html' };
    const expectedWebContents = { mainFrame };
    assert.equal(
      contract.assertTrustedRendererSender(
        { sender: expectedWebContents, senderFrame: mainFrame },
        expectedWebContents,
        policy.APP_ORIGIN
      ),
      true
    );
    assert.throws(
      () => contract.assertTrustedRendererSender(
        { sender: {}, senderFrame: mainFrame },
        expectedWebContents,
        policy.APP_ORIGIN
      ),
      { code: contract.IPC_ERROR_CODES.ACCESS_DENIED }
    );
    const foreignFrame = { url: 'https://127.0.0.1:1/foreign' };
    const foreignWebContents = { mainFrame: foreignFrame };
    assert.throws(
      () => contract.assertTrustedRendererSender(
        { sender: foreignWebContents, senderFrame: foreignFrame },
        foreignWebContents,
        policy.APP_ORIGIN
      ),
      { code: contract.IPC_ERROR_CODES.ACCESS_DENIED }
    );

    const rendererApi = createRendererApi({
      invoke: async (_channel, request) => contract.createBridgeStatusSuccess(request.requestId),
      randomUUID: () => 'req-imp104-renderer',
    });
    assert.deepEqual(
      Object.keys(rendererApi).sort(),
      ['apiVersion', 'ipcBaseline', 'productionUtility', 'securityBaseline', 'studio'].sort()
    );
    assert.deepEqual(Object.keys(rendererApi.productionUtility), ['getBridgeStatus']);
    assert.deepEqual(Object.keys(rendererApi.studio), ['getApplicationReadModel']);
    assert.equal(Object.isFrozen(rendererApi), true);
    assert.equal(rendererApi.invoke, undefined);
    assert.equal(rendererApi.safeStorage, undefined);
    assert.equal(rendererApi.credentialBroker, undefined);
    assert.equal(rendererApi.productionUtility.issueLease, undefined);
    assert.equal(rendererApi.productionUtility.getCredential, undefined);
    const status = await rendererApi.productionUtility.getBridgeStatus();
    assert.equal(status.ok, true);

    const fakeHandlers = new Map();
    const fakeIpcMain = {
      handle(channel, handler) {
        assert.equal(fakeHandlers.has(channel), false);
        fakeHandlers.set(channel, handler);
      },
      removeHandler(channel) {
        fakeHandlers.delete(channel);
      },
    };
    installProductionIpcHandlers({
      ipcMain: fakeIpcMain,
      webContents: expectedWebContents,
      appOrigin: policy.APP_ORIGIN,
      bridge: {
        async getBridgeStatus(request) {
          return contract.createBridgeStatusSuccess(request.requestId);
        },
        async getApplicationReadModel() {
          throw new Error('synthetic internal failure');
        },
      },
    });
    const handler = fakeHandlers.get(contract.CHANNELS.GET_BRIDGE_STATUS);
    const denied = await handler(
      { sender: {}, senderFrame: mainFrame },
      { apiVersion: 1, requestId: 'req-imp104-denied', secret: 'SYNTHETIC_TEST_VALUE' }
    );
    assert.equal(denied.ok, false);
    assert.equal(denied.error.code, contract.IPC_ERROR_CODES.ACCESS_DENIED);
    assert.equal(denied.error.message, 'Request could not be completed.');
    assert.doesNotMatch(JSON.stringify(denied), /SYNTHETIC_TEST_VALUE|secret/i);
  }
);

test(
  'packaged Windows Electron proves DPAPI safeStorage without exposing a secret or writing the vault',
  { skip: !packageTestsEnabled || process.platform !== 'win32' },
  async () => {
    const { packageDir, executable } = packagePaths();
    assert.equal(await exists(executable), true, 'packaged Windows executable must exist');
    const artifactRoot = path.resolve(
      process.env.FLOWKIT_SECURITY_ARTIFACT_DIR || path.resolve(packageDir, '..')
    );
    const userDataPath = path.join(artifactRoot, 'runtime-user-data');
    const relativeUserData = path.relative(artifactRoot, userDataPath);
    assert.ok(
      relativeUserData !== '..' && !relativeUserData.startsWith('..' + path.sep),
      'runtime user-data must remain inside the isolated artifact root'
    );
    await fs.rm(userDataPath, { recursive: true, force: true });
    await fs.mkdir(userDataPath, { recursive: true });

    const child = spawn(
      executable,
      ['--user-data-dir=' + userDataPath, '--flowkit-security-self-test'],
      { cwd: packageDir, windowsHide: true, stdio: 'ignore' }
    );
    const exit = await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        child.kill();
        reject(new Error('packaged safeStorage self-test timed out'));
      }, 30000);
      timeout.unref();
      child.once('error', (error) => {
        clearTimeout(timeout);
        reject(error);
      });
      child.once('exit', (code, signal) => {
        clearTimeout(timeout);
        resolve({ code, signal });
      });
    });
    assert.equal(exit.code, 0, 'packaged safeStorage self-test exited ' + exit.code + ' signal=' + exit.signal);

    const reportPath = path.join(userDataPath, 'flowkit-security-self-test.json');
    const report = JSON.parse(await fs.readFile(reportPath, 'utf8'));
    assert.equal(report.marker, 'FLOWKIT_PACKAGED_SECURITY_SELF_TEST');
    assert.equal(report.status, 'PASS');
    assert.equal(report.failureCode, null);
    assert.equal(report.platform, 'win32');
    assert.equal(report.electronVersion, '44.7.0');
    assert.equal(report.safeStorageAvailable, true);
    assert.notEqual(report.safeStorageBackendReported, 'basic_text');
    assert.equal(report.syntheticRoundTrip, true);
    assert.equal(report.ciphertextDistinct, true);
    assert.equal(report.credentialVaultPresentBefore, false);
    assert.equal(report.credentialVaultPresentAfter, false);
    assert.doesNotMatch(JSON.stringify(report), /FLOWKIT_IMP104_SYNTHETIC_CANARY_ONLY/);
    assert.equal(await exists(path.join(userDataPath, 'credential-vault-v1.json')), false);

    const localStatePath = path.join(userDataPath, 'Local State');
    const localState = JSON.parse(await fs.readFile(localStatePath, 'utf8'));
    const encodedProtectedKey = localState.os_crypt && localState.os_crypt.encrypted_key;
    assert.equal(typeof encodedProtectedKey, 'string', 'Chromium Local State must contain an encrypted OS crypt key');
    const protectedKey = Buffer.from(encodedProtectedKey, 'base64');
    assert.equal(
      protectedKey.subarray(0, 5).toString('ascii'),
      'DPAPI',
      'Windows Local State key must use the DPAPI-protected key envelope'
    );
    const dpapiBlob = protectedKey.subarray(5);
    assert.ok(dpapiBlob.length > 0, 'DPAPI-protected key blob must not be empty');
    const dpapiBlobPath = path.join(userDataPath, 'flowkit-security-self-test-dpapi-blob.bin');
    await fs.writeFile(dpapiBlobPath, dpapiBlob);
    let dpapiVerified = false;
    try {
      const encodedPath = Buffer.from(dpapiBlobPath, 'utf8').toString('base64');
      const psScript = [
        "$p=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('" + encodedPath + "'))",
        'Add-Type -AssemblyName System.Security',
        '$b=[IO.File]::ReadAllBytes($p)',
        '$plain=[System.Security.Cryptography.ProtectedData]::Unprotect($b,$null,[System.Security.Cryptography.DataProtectionScope]::CurrentUser)',
        "if($plain.Length -eq 32){'DPAPI_PROOF=PASS';exit 0}else{'DPAPI_PROOF=FAIL';exit 1}",
      ].join('; ');
      const encodedScript = Buffer.from(psScript, 'utf16le').toString('base64');
      const dpapi = spawnSync(
        'powershell.exe',
        ['-NoProfile', '-NonInteractive', '-EncodedCommand', encodedScript],
        { encoding: 'utf8', timeout: 15000, windowsHide: true }
      );
      assert.equal(dpapi.error, undefined, 'native Windows DPAPI verification process must start');
      assert.equal(dpapi.status, 0, 'native DPAPI verification failed: ' + dpapi.stdout + dpapi.stderr);
      assert.match(dpapi.stdout, /DPAPI_PROOF=PASS/);
      dpapiVerified = true;
    } finally {
      if (dpapiVerified) {
        await fs.rm(dpapiBlobPath, { force: true });
      }
    }
  }
);
