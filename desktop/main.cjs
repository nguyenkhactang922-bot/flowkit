'use strict';

const { app, BrowserWindow, ipcMain, net, protocol, utilityProcess } = require('electron');
const path = require('path');
const { pathToFileURL } = require('url');
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

app.whenReady().then(() => {
  registerAppProtocol();
  productionUtilityBridge = new ProductionUtilityBridge({
    utilityProcess,
    entryPath: UTILITY_ENTRY,
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
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
