"""从 packages/*.difypkg 自动生成 README.md 插件列表。"""

import glob
import os
import re
import zipfile

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGES_DIR = os.path.join(ROOT, "packages")
README_PATH = os.path.join(ROOT, "README.md")
GITHUB_RAW = "https://github.com/yidaowanliu-del/dify-plugins/raw/main/packages"


def _get_text(obj, key):
    if not isinstance(obj, dict):
        return str(obj)
    return obj.get("zh_Hans") or obj.get("en_US", "")


def _clean_desc(text: str) -> str:
    """清理描述：取第一行、限制长度。"""
    text = text.split("\n")[0].strip()
    return text[:60] + "…" if len(text) > 60 else text


def collect_plugins():
    plugins = []
    for pkg_path in sorted(glob.glob(os.path.join(PACKAGES_DIR, "*.difypkg"))):
        filename = os.path.basename(pkg_path)
        try:
            with zipfile.ZipFile(pkg_path) as z:
                manifest = yaml.safe_load(z.read("manifest.yaml"))
        except Exception as e:
            print(f"  [跳过] {filename}: {e}")
            continue

        label = _get_text(manifest.get("label"), "zh_Hans") or filename
        desc = _clean_desc(_get_text(manifest.get("description"), "zh_Hans") or "")
        version = manifest.get("version", "0.0.0")

        plugins.append({
            "label": label,
            "desc": desc,
            "filename": filename,
        })
    return plugins


def generate_table(plugins):
    lines = [
        "## 插件列表",
        "",
        "| 插件 | 说明 | 下载 |",
        "|------|------|------|",
    ]
    for p in plugins:
        url = f"{GITHUB_RAW}/{p['filename']}"
        lines.append(f"| **{p['label']}** | {p['desc']} | [下载]({url}) |")
    return lines


def update_readme(plugins):
    with open(README_PATH, encoding="utf-8") as f:
        content = f.read()

    table_lines = generate_table(plugins)
    new_section = "\n".join(table_lines) + "\n"

    # 替换从 "## 插件列表" 到下一个 "## " 之前的内容
    pattern = re.compile(r"## 插件列表\n.*?(?=\n## |\Z)", re.DOTALL)
    if pattern.search(content):
        content = pattern.sub(new_section, content)
    else:
        content += "\n" + new_section

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"已更新 {len(plugins)} 个插件到 README.md")


def main():
    plugins = collect_plugins()
    if not plugins:
        print("packages/ 目录下没有找到 .difypkg 文件")
        return
    update_readme(plugins)


if __name__ == "__main__":
    main()
