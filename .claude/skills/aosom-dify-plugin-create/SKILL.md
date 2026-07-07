---
name: aosom-dify-plugin-create
description: Create new aosom Dify plugins (Tool type). Follows project conventions: UV workspace, utils/tools/provider structure, YAML patterns. Use when starting a new plugin project.
---

## Prerequisites

- `dify` CLI installed (`brew install dify`)
- Project root has UV workspace (`pyproject.toml` with `[tool.uv.workspace]`)

## Steps

### 1. Initialize with CLI

```bash
cd /path/to/dify-plugins
dify plugin init
```

- Plugin name: `aosom_lark_xxx` (snake_case)
- Author: `aosom`
- Type: `tool`
- Permissions: only enable `tool` backwards invocation, keep others disabled

### 2. Add to UV workspace

Edit root `pyproject.toml`:

```toml
[tool.uv.workspace]
members = ["aosom-lark-xxx"]
```

Sync dependencies:

```bash
uv sync
```

### 3. Restructure files

Replace the generated template files with clean names:

```
aosom-lark-xxx/
├── utils/
│   ├── __init__.py
│   └── lark_xxx.py          ← LarkClient subclass or standalone client
├── provider/
│   ├── provider.yaml        ← credentials config (app_id, app_secret, base_url)
│   └── provider.py          ← Provider class
├── tools/
│   ├── __init__.py
│   ├── xxx.yaml             ← tool definition
│   └── xxx.py               ← tool implementation
├── manifest.yaml
├── main.py
├── requirements.txt         ← dify_plugin + httpx
└── pyproject.toml            ← keep for UV workspace
```

### 4. Provider pattern

**provider.yaml** — credentials_for_provider:
- `lark_app_id`: text-input, required
- `lark_app_secret`: secret-input, required
- `lark_base_url`: select, optional, default `https://open.feishu.cn`, options include `https://open.larksuite.com`

**provider.py** — `_validate_credentials`: test tenant_access_token via `POST /open-apis/auth/v3/tenant_access_token/internal`

### 5. Tool code pattern

- `utils/lark_xxx.py` — `LarkClient` sync class (httpx.Client, token management, retry on code 90217, `build_client()` helper)
- `tools/xxx.py` — `SendXxxTool(Tool)` class, import `build_client` from utils, handle `isinstance(content, dict)` → `json.dumps()` for content normalization
- `tools/xxx.yaml` — `identity.name` matches method name, `type: object` for content param, use llm form for key params

### 6. YAML conventions

- `manifest.yaml` `label`/`description`: concise bilingual (en_US + zh_Hans)
- `author`: `aosom`
- `extra.python.source`: points to the correct file path
- `msg_type` option labels: use English values (text, post, image, interactive)

### 7. Package name

```bash
dify plugin package aosom-lark-xxx
```
Output will be `aosom-lark-xxx.difypkg`. After packaging, rename to `{name}_{version}.difypkg` and move to `packages/`.

## Reference

See `aosom-lark-message` for a complete working example.
