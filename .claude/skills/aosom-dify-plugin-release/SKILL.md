---
name: aosom-dify-plugin-release
description: Release aosom Dify plugins. Package, version, update README, commit, and push. Use when the plugin code is ready to ship.
---

## Release Steps

### 1. Bump version

In `manifest.yaml`, increment the top-level `version` field (line 1):

```yaml
version: 0.0.2   # was 0.0.1
```

Also update `pyproject.toml` version to match.

### 2. Package

```bash
cd /path/to/dify-plugins
dify plugin package aosom-lark-xxx
```

### 3. Move to packages/ with correct name

Convention: `{name}_{version}.difypkg`

```bash
mv aosom-lark-xxx.difypkg packages/aosom-lark-xxx_0.0.2.difypkg
```

### 4. Update README

Update the download link in `README.md`:

```markdown
| **aosom-lark-xxx** | description | [下载](https://github.com/yidaowanliu-del/dify-plugins/raw/main/packages/aosom-lark-xxx_0.0.2.difypkg) |
```

### 5. Commit

```bash
git add packages/ README.md aosom-lark-xxx/manifest.yaml aosom-lark-xxx/pyproject.toml
git commit -m "feat: release aosom-lark-xxx v0.0.2"
```

### 6. Push

```bash
git push
```

## Version Convention

- `0.0.1` — initial release
- `0.0.x` — bug fixes / minor improvements
- `0.1.x` — new features
- `1.0.0` — stable release
