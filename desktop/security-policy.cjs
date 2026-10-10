'use strict';

const path = require('path');

const APP_SCHEME = 'flowkit';
const APP_HOST = 'app';
const APP_ORIGIN = `${APP_SCHEME}://${APP_HOST}`;

function isAllowedAppUrl(candidate) {
  try {
    const url = new URL(candidate);
    return url.protocol === `${APP_SCHEME}:` && url.hostname === APP_HOST;
  } catch (_error) {
    return false;
  }
}

function resolveRendererPath(rendererRoot, requestUrl) {
  if (!isAllowedAppUrl(requestUrl)) {
    return null;
  }

  const url = new URL(requestUrl);
  const rawPath = decodeURIComponent(url.pathname || '/index.html');
  const relative = rawPath.replace(/^\/+/, '') || 'index.html';
  const root = path.resolve(rendererRoot);
  const resolved = path.resolve(root, path.normalize(relative));
  if (resolved !== root && !resolved.startsWith(root + path.sep)) {
    return null;
  }
  return resolved;
}

function installNavigationGuards(webContents) {
  webContents.on('will-navigate', (event, targetUrl) => {
    if (!isAllowedAppUrl(targetUrl)) {
      event.preventDefault();
    }
  });

  webContents.setWindowOpenHandler(() => ({ action: 'deny' }));

  webContents.on('will-attach-webview', (event) => {
    event.preventDefault();
  });
}

module.exports = {
  APP_SCHEME,
  APP_HOST,
  APP_ORIGIN,
  isAllowedAppUrl,
  resolveRendererPath,
  installNavigationGuards,
};
