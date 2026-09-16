from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND = PROJECT_ROOT / "frontend"


def _package_json() -> dict:
    return json.loads(
        (FRONTEND / "package.json").read_text(encoding="utf-8")
    )


def _package_lock() -> dict:
    return json.loads(
        (FRONTEND / "package-lock.json").read_text(encoding="utf-8")
    )


def test_h8d2_frontend_declares_quality_scripts():
    package = _package_json()
    scripts = package["scripts"]

    assert package["packageManager"] == "npm@12.0.2"
    assert package["engines"]["node"] == "^22.22.2"
    assert scripts["lint"].startswith("eslint ")
    assert "tsconfig.app.json" in scripts["typecheck"]
    assert "tsconfig.node.json" in scripts["typecheck"]
    assert scripts["test"] == "vitest run"
    assert "vite build" in scripts["build"]


def test_h8d2_frontend_quality_tools_are_exactly_pinned():
    package = _package_json()
    dev = package["devDependencies"]

    expected = {
        "@babel/core": "8.0.5",
        "@babel/eslint-parser": "8.0.5",
        "@eslint/js": "10.0.1",
        "eslint": "10.10.0",
        "eslint-plugin-react-hooks": "7.1.1",
        "globals": "17.12.0",
        "typescript": "7.0.2",
        "vite": "8.2.2",
        "vitest": "5.0.0",
    }

    for dependency, version in expected.items():
        assert dev[dependency] == version

    assert "@babel/preset-typescript" not in dev


def test_h8d2_eslint_uses_supported_babel_parser_syntax_plugins():
    content = (FRONTEND / "eslint.config.js").read_text(encoding="utf-8")

    assert '@babel/eslint-parser' in content
    assert 'plugins: ["typescript", "jsx"]' in content
    assert '@babel/preset-typescript' not in content
    assert 'react-hooks/rules-of-hooks' in content
    assert 'react-hooks/exhaustive-deps' in content
    assert 'typescript-eslint' not in content


def test_h8d2_cross_platform_lock_contains_required_native_packages():
    lock = _package_lock()
    packages = lock["packages"]

    required = {
        "node_modules/@typescript/typescript-linux-x64",
        "node_modules/@typescript/typescript-win32-x64",
        "node_modules/@rolldown/binding-linux-x64-gnu",
        "node_modules/@rolldown/binding-win32-x64-msvc",
        "node_modules/lightningcss-linux-x64-gnu",
        "node_modules/lightningcss-win32-x64-msvc",
    }

    assert required.issubset(packages)


def test_h8d2_lockfile_is_v3_and_matches_frontend_package_identity():
    lock = _package_lock()

    assert lock["lockfileVersion"] == 3
    assert lock["name"] == "buildshield-ci-frontend"
    assert lock["version"] == "0.0.0-h3a"


def test_h8d2_dockerfile_uses_supported_clean_frontend_install():
    content = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM node:22.23.2-bookworm-slim AS frontend-builder" in content
    assert "npm install --global npm@12.0.2 --no-audit --no-fund" in content
    assert "npm ci --ignore-scripts --no-audit --no-fund" in content
    assert "npm ls --all" in content
    assert "--legacy-peer-deps" not in content
    assert "npm run typecheck && npm run build" in content
    assert "npm pack" not in content
    assert "install_native_package" not in content
    assert "@typescript/typescript-linux-x64" not in content
    assert "@rolldown/binding-linux-x64-gnu" not in content
    assert "lightningcss-linux-x64-gnu" not in content


def test_h8d2_lint_toolchain_matches_node_and_peer_compatibility():
    package = _package_json()
    dev = package["devDependencies"]

    assert package["engines"]["node"] == "^22.22.2"
    assert package["packageManager"] == "npm@12.0.2"
    assert dev["@testing-library/dom"] == "10.4.1"

    assert dev["@babel/eslint-parser"] == "8.0.5"
    assert dev["@babel/core"] == "8.0.5"
    assert "@babel/preset-typescript" not in dev
    assert dev["eslint"] == "10.10.0"
    assert dev["@eslint/js"] == "10.0.1"


def test_h8d2_required_testing_library_peer_is_explicit():
    package = _package_json()
    dev = package["devDependencies"]

    # React Testing Library v16 requires @testing-library/dom as a peer.
    # Keep the required peer explicit even though clean npm peer resolution
    # now succeeds without the former legacy-peer-deps workaround.
    assert dev["@testing-library/dom"] == "10.4.1"
    assert dev["@testing-library/react"] == "16.3.3"
