'use strict';

const { app, BrowserWindow, ipcMain, net, protocol, safeStorage, utilityProcess } = require('electron');
const path = require('path');
const fs = require('node:fs');
const { pathToFileURL } = require('url');
const { SafeStorageCredentialBroker } = require('./credential-broker.cjs');
const { installProductionIpcHandlers } = require('./ipc-main.cjs');
const { ProductionUtilityBridge } = require('./production-utility-bridge.cjs');
const {
  APP_SCHEME,
  APP_ORIGIN,
  isAllowedAppUrl,
  resolveRendererPath,
  installNavigationGuards,
} = require('./security-policy.cjs');

protocol.registerSchemesAsPrivileged([
  {
    scheme: APP_SCHEME,
    privileges: {
      standard: true,
      secure: true,
      supportFetchAPI: true,
      corsEnabled: false,
      stream: true,
    },
  },
]);

const RENDERER_ROOT = path.join(__dirname, 'renderer');
const UTILITY_ENTRY = path.join(__dirname, 'utility-entry.cjs');
const SECURITY_SELF_TEST_ARG = '--flowkit-security-self-test';
const SECURITY_SELF_TEST_CANARY = 'FLOWKIT_IMP104_SYNTHETIC_CANARY_ONLY';
let credentialBroker = null;
let productionUtilityBridge = null;
let ipcRegistration = null;

function registerAppProtocol() {
  protocol.handle(APP_SCHEME, async (request) => {
    if (!isAllowedAppUrl(request.url)) {
      return new Response('Forbidden', { status: 403 });
    }

    const filePath = resolveRendererPath(RENDERER_ROOT, request.url);
    if (!filePath) {
      return new Response('Forbidden', { status: 403 });
    }

    return net.fetch(pathToFileURL(filePath).toString());
  });
}

function createMainWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 960,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      webSecurity: true,
      allowRunningInsecureContent: false,
      experimentalFeatures: false,
      webviewTag: false,
      navigateOnDragDrop: false,
    },
  });

  installNavigationGuards(win.webContents);
  if (ipcRegistration) {
    ipcRegistration.dispose();
  }
  ipcRegistration = installProductionIpcHandlers({
    ipcMain,
    webContents: win.webContents,
    appOrigin: APP_ORIGIN,
    bridge: productionUtilityBridge,
  });

  win.once('closed', () => {
    if (ipcRegistration) {
      ipcRegistration.dispose();
      ipcRegistration = null;
    }
  });
  win.once('ready-to-show', () => win.show());
  win.loadURL(`${APP_ORIGIN}/index.html`);
  return win;
}

async function runPackagedSecuritySelfTest() {
  const userDataPath = app.getPath('userData');
  fs.mkdirSync(userDataPath, { recursive: true });
  const vaultPath = path.join(userDataPath, 'credential-vault-v1.json');
  const credentialVaultPresentBefore = fs.existsSync(vaultPath);
  const safeStorageAvailable = safeStorage.isEncryptionAvailable();
  const safeStorageBackendApiAvailable =
    typeof safeStorage.getSelectedStorageBackend === 'function';
  let safeStorageBackendReported = 'not-reported-on-windows';
  let ciphertext = null;
  let syntheticRoundTrip = false;
  let ciphertextDistinct = false;
  let failureCode = null;

  try {
    if (safeStorageBackendApiAvailable) {
      safeStorageBackendReported = safeStorage.getSelectedStorageBackend();
      if (safeStorageBackendReported === 'basic_text') {
        failureCode = 'UNSAFE_STORAGE_BACKEND_REPORTED';
      }
    }

    if (!safeStorageAvailable) {
      failureCode = failureCode || 'SAFE_STORAGE_UNAVAILABLE';
    } else {
      ciphertext = safeStorage.encryptString(SECURITY_SELF_TEST_CANARY);
      syntheticRoundTrip = safeStorage.decryptString(ciphertext) === SECURITY_SELF_TEST_CANARY;
      ciphertextDistinct =
        Buffer.isBuffer(ciphertext) &&
        !ciphertext.equals(Buffer.from(SECURITY_SELF_TEST_CANARY, 'utf8'));
      if (!syntheticRoundTrip || !ciphertextDistinct) {
        failureCode = failureCode || 'SAFE_STORAGE_ROUND_TRIP_FAILED';
      }
    }
  } catch (_error) {
    failureCode = failureCode || 'SAFE_STORAGE_OPERATION_FAILED';
  }

  if (process.platform !== 'win32') {
    failureCode = failureCode || 'UNSUPPORTED_TEST_PLATFORM';
  }
  const credentialVaultPresentAfter = fs.existsSync(vaultPath);
  if (credentialVaultPresentBefore || credentialVaultPresentAfter) {
    failureCode = failureCode || 'CREDENTIAL_VAULT_TOUCHED';
  }
  const report = {
    schemaVersion: 1,
    marker: 'FLOWKIT_PACKAGED_SECURITY_SELF_TEST',
    status: failureCode === null ? 'PASS' : 'FAIL',
    failureCode,
    appVersion: app.getVersion(),
    electronVersion: process.versions.electron,
    platform: process.platform,
    safeStorageAvailable,
    safeStorageBackendApiAvailable,
    safeStorageBackendReported,
    syntheticRoundTrip,
    ciphertextDistinct,
    credentialVaultPresentBefore,
    credentialVaultPresentAfter,
  };
  const reportPath = path.join(userDataPath, 'flowkit-security-self-test.json');
  await fs.promises.writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  console.log(`FLOWKIT_PACKAGED_SECURITY_SELF_TEST=${report.status} ${JSON.stringify(report)}`);

  if (report.status === 'PASS') {
    app.quit();
  } else {
    app.exit(1);
  }
}

app.whenReady().then(async () => {
  if (process.argv.includes(SECURITY_SELF_TEST_ARG)) {
    try {
      await runPackagedSecuritySelfTest();
    } catch (_error) {
      console.error('FLOWKIT_PACKAGED_SECURITY_SELF_TEST=FAIL');
      app.exit(1);
    }
    return;
  }
  registerAppProtocol();
  credentialBroker = new SafeStorageCredentialBroker({
    safeStorage,
    vaultPath: path.join(app.getPath('userData'), 'credential-vault-v1.json'),
  });
  productionUtilityBridge = new ProductionUtilityBridge({
    utilityProcess,
    entryPath: UTILITY_ENTRY,
    credentialBroker,
  });
  createMainWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on('before-quit', () => {
  if (ipcRegistration) {
    ipcRegistration.dispose();
    ipcRegistration = null;
  }
  if (productionUtilityBridge) {
    productionUtilityBridge.close();
    productionUtilityBridge = null;
  }
  if (credentialBroker) {
    credentialBroker.close();
    credentialBroker = null;
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
