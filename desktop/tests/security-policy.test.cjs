'use strict';

const assert = require('node:assert/strict');
const path = require('node:path');
const test = require('node:test');
const {
  APP_ORIGIN,
  isAllowedAppUrl,
  resolveRendererPath,
  installNavigationGuards,
} = require('../security-policy.cjs');

test('only the privileged app origin is accepted', () => {
  assert.equal(isAllowedAppUrl(`${APP_ORIGIN}/index.html`), true);
  assert.equal(isAllowedAppUrl(`${APP_ORIGIN}/assets/app.js`), true);
  assert.equal(isAllowedAppUrl('https://example.com/'), false);
  assert.equal(isAllowedAppUrl('file:///tmp/index.html'), false);
  assert.equal(isAllowedAppUrl('not a url'), false);
});

test('renderer path resolution fails closed on traversal and foreign schemes', () => {
  const root = path.resolve('desktop', 'renderer');
  assert.equal(
    resolveRendererPath(root, `${APP_ORIGIN}/index.html`),
    path.join(root, 'index.html')
  );
  assert.equal(resolveRendererPath(root, `${APP_ORIGIN}/%2e%2e%2fsecret.txt`), null);
  assert.equal(resolveRendererPath(root, 'https://example.com/index.html'), null);
});

test('navigation guards deny external navigation, all new windows, and webviews', () => {
  const handlers = new Map();
  let openHandler;
  const webContents = {
    on(name, handler) {
      handlers.set(name, handler);
    },
    setWindowOpenHandler(handler) {
      openHandler = handler;
    },
  };

  installNavigationGuards(webContents);

  let prevented = false;
  handlers.get('will-navigate')(
    { preventDefault() { prevented = true; } },
    'https://example.com/phish'
  );
  assert.equal(prevented, true);

  prevented = false;
  handlers.get('will-navigate')(
    { preventDefault() { prevented = true; } },
    `${APP_ORIGIN}/next`
  );
  assert.equal(prevented, false);

  assert.deepEqual(openHandler({ url: `${APP_ORIGIN}/popup` }), { action: 'deny' });
  assert.deepEqual(openHandler({ url: 'https://example.com/' }), { action: 'deny' });

  let webviewPrevented = false;
  handlers.get('will-attach-webview')({
    preventDefault() { webviewPrevented = true; },
  });
  assert.equal(webviewPrevented, true);
});
