'use strict';

const { app, BrowserWindow, net, protocol } = require('electron');
const path = require('path');
const { pathToFileURL } = require('url');
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
  win.once('ready-to-show', () => win.show());
  win.loadURL(`${APP_ORIGIN}/index.html`);
  return win;
}

app.whenReady().then(() => {
  registerAppProtocol();
  createMainWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
