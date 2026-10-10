"""IMP-070 Electron host shell security baseline tests."""

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
        "security-policy.cjs",
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


def test_preload_exposes_no_generic_privileged_bridge():
    source = _text("preload.cjs")
    assert "contextBridge" in source
    assert "ipcRenderer" not in source
    assert "child_process" not in source
    assert "require('fs')" not in source
    assert "require(\"fs\")" not in source
    assert "shell" not in source
    assert "flowkitHost" in source


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
