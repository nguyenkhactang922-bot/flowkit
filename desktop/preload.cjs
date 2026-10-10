'use strict';

const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld(
  'flowkitHost',
  Object.freeze({
    apiVersion: 1,
    securityBaseline: 'imp-070-v1',
  })
);
