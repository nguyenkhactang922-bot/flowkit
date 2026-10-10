"""IMP-070/IMP-071 Electron host shell and typed IPC security tests."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DESKTOP = ROOT / "desktop"


def _text(name: str) -> str:
    return (DESKTOP / name).read_text(encoding="utf-8")


def test_desktop_package_pins_supported_electron_and_packaging_skeleton():
    package = json.loads(_text("package.json"))
    assert package["main"] == "main.cjs"
    assert package["devDependencies"]["electron"] == "44.7.0"
    assert package["devDependencies"]["electron-builder"] == "26.15.3"
    assert package["build"]["asar"] is True
    assert package["build"]["appId"] == "com.flowkit.studio"
    assert package["build"]["win"]["target"] == ["nsis"]
    assert set(package["build"]["files"]) == {
        "main.cjs",
        "preload.cjs",
        "preload-api.cjs",
        "security-policy.cjs",
        "ipc-contract.cjs",
        "ipc-main.cjs",
        "production-utility-bridge.cjs",
        "utility-entry.cjs",
        "renderer/**/*",
    }


def test_browserwindow_security_flags_are_explicit_and_fail_closed():
    source = _text("main.cjs")
    required = {
        "nodeIntegration": "false",
        "contextIsolation": "true",
        "sandbox": "true",
        "webSecurity": "true",
        "allowRunningInsecureContent": "false",
        "experimentalFeatures": "false",
        "webviewTag": "false",
        "navigateOnDragDrop": "false",
    }
    for key, value in required.items():
        assert re.search(rf"\b{key}\s*:\s*{value}\b", source), key


def test_main_uses_custom_secure_protocol_and_not_file_loading_or_external_shell():
    source = _text("main.cjs")
    assert "protocol.registerSchemesAsPrivileged" in source
    assert "secure: true" in source
    assert "protocol.handle(APP_SCHEME" in source
    assert "win.loadURL(`${APP_ORIGIN}/index.html`)" in source
    assert "loadFile(" not in source
    assert "shell.openExternal" not in source
    assert "require('shell')" not in source


def test_preload_exposes_only_bounded_typed_ipc_capability():
    preload = _text("preload.cjs")
    api = _text("preload-api.cjs")
    contract = _text("ipc-contract.cjs")

    assert "contextBridge.exposeInMainWorld('flowkitHost', rendererApi)" in preload
    assert "ipcRenderer.invoke(channel, request)" in preload
    assert "flowkitHost', ipcRenderer" not in preload
    assert "exposeInMainWorld('ipcRenderer'" not in preload
    assert 'exposeInMainWorld("ipcRenderer"' not in preload

    assert "getBridgeStatus" in api
    assert "ipcRenderer" not in api
    assert "child_process" not in api
    assert "require('fs')" not in api
    assert 'require("fs")' not in api
    assert "shell" not in api
    assert "flowkit:generic:invoke" not in contract
    assert "flowkit:utility:get-bridge-status" in contract


def test_renderer_declares_restrictive_csp():
    source = _text("renderer/index.html")
    for directive in (
        "default-src 'self'",
        "script-src 'self'",
        "object-src 'none'",
        "base-uri 'none'",
        "frame-ancestors 'none'",
    ):
        assert directive in source


def test_navigation_window_and_webview_policy_behavior():
    completed = subprocess.run(
        ["node", "--test", "desktop/tests/security-policy.test.cjs"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_typed_ipc_negative_contract_behavior():
    completed = subprocess.run(
        ["node", "--test", "desktop/tests/ipc-contract.test.cjs"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
