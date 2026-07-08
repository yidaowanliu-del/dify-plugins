# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dify 插件包合集。包含已有的 `langgenius-feishu` 系列插件和自建的 `aosom-lark-*` 系列插件。

## Architecture

### Project Layout

```
dify-plugins/
├── pyproject.toml        # UV workspace 根配置
├── uv.lock               # 依赖锁定
├── .python-version       # Python 3.13
├── packages/             # 已打包的 .difypkg 文件
└── aosom-lark-xxx/       # 每个插件一个目录（workspace member）
    ├── manifest.yaml      # 插件元信息（扁平格式）
    ├── main.py            # Plugin(DifyPluginEnv()) 入口
    ├── requirements.txt   # Dify daemon 依赖声明
    ├── pyproject.toml     # UV workspace 成员配置
    ├── provider/
    │   ├── provider.yaml  # 凭证配置（app_id, app_secret, base_url）
    │   └── provider.py    # LarkMessageProvider 凭证校验
    ├── tools/
    │   ├── xxx.yaml       # 工具定义（参数、描述）
    │   └── xxx.py         # SendXxxTool 实现
    └── utils/
        └── lark_client.py # LarkClient（共享 HTTP 客户端实例）
```

### Plugin Code Pattern

- **LarkClient** (`utils/lark_client.py`): 同步 httpx 客户端，自动 token 管理、90217 限流重试。通过 `get_client()` 模块级缓存共享实例。
- **Provider** (`provider/`): `_validate_credentials` 测试 tenant_access_token 有效性。
- **Tools** (`tools/`): `SendXxxTool._invoke()` → `get_client(credentials).send_xxx()`。`content` 参数兼容 dict/string 两种输入。
- 凭证 `lark_app_id` + `lark_app_secret` + `lark_base_url`（可选，默认飞书国内站）。

### 命名约定

- 包名: `aosom-lark-xxx`（manifest.yaml `name` 字段）
- 版本: `0.0.x` 递增
- `.difypkg` 文件: `{name}_{version}.difypkg` → `packages/`
- 内置 skill: `/aosom-dify-plugin-create` 创建新插件, `/aosom-dify-plugin-release` 发布

## Commands

```bash
# 打包插件
dify plugin package aosom-lark-xxx

# 重命名并移动到 packages/
mv aosom-lark-xxx.difypkg packages/aosom-lark-xxx_0.0.x.difypkg

# 本地调试
cd aosom-lark-xxx && uv run python -m main

# 添加依赖（根 workspace）
uv add <package>

# 验证包
dify plugin checksum packages/aosom-lark-xxx_0.0.x.difypkg
```

## Important Rules

- `manifest.yaml` 使用扁平格式（`author`/`name`/`version` 在顶层，参考 `langgenius-feishu_message`）
- `resource.memory` 保持 `1048576`（1MB）
- `requirements.txt` 使用 `dify-plugin>=0.9.0`
- 更新版本时同步更新 manifest.yaml、pyproject.toml、README.md 下载链接
- 旧版本 `.difypkg` 文件需要清理
