#!/usr/bin/env python3
"""fnOS 应用源（fnpack.json）维护工具。

用法示例:
  py scripts/depot.py add-app hello-world --name 示例应用 --desc "第一个应用" --cat 系统工具
  py scripts/depot.py add-release hello-world 1.0.0 --x86 dist/hello-world-1.0.0-x86.fpk --arm dist/hello-world-1.0.0-arm.fpk --changelog "初始版本"
  py scripts/depot.py validate
  py scripts/depot.py gen-readme
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import struct
import sys
import urllib.request
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FNPACK_PATH = ROOT / "fnpack.json"
README_PATH = ROOT / "README.md"

FIXED_CATEGORIES = ["影音娱乐", "系统工具", "编程开发", "AI赋能", "生活服务", "智能智控", "教育学习", "游戏地带", "硬件驱动"]
PLATFORMS = {"x86", "arm", "all"}
RUN_AS_VALUES = {"package", "root"}
INSTALL_TYPE_VALUES = {"", "root"}
GROUP_LETTERS = [("A–F", "abcdef"), ("G–L", "ghijkl"), ("M–R", "mnopqr"), ("S–Z", "stuvwxyz")]

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def load_fnpack() -> dict:
    with FNPACK_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def save_fnpack(data: dict) -> None:
    with FNPACK_PATH.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def github_owner_repo(data: dict):
    """从 source_info.homepage 解析 (owner, repo)，未配置时返回 None。"""
    homepage = data.get("source_info", {}).get("homepage", "")
    m = re.match(r"^https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", homepage)
    return (m.group(1), m.group(2)) if m else None


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def hash_file(path: Path):
    h = hashlib.sha256()
    size = 0
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def fetch_remote_info(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "fnos-depot-tool/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        blob = resp.read()
    return hashlib.sha256(blob).hexdigest(), len(blob)


def placeholder_png(path: Path, w: int, h: int) -> None:
    """生成一张带白边的渐变色占位图，仅用于目录骨架。"""
    base = (36, 130, 156)
    rows = bytearray()
    for y in range(h):
        rows.append(0)  # PNG filter: None
        border = y < h // 12 or y >= h - h // 12
        for x in range(w):
            if border or x < w // 12 or x >= w - w // 12:
                rgb = (255, 255, 255)
            else:
                t = (x + y) / (w + h)
                rgb = (int(base[0] + 60 * t) & 255,
                       int(base[1] - 50 * t) & 255,
                       int(base[2] - 70 * t) & 255)
            rows += bytes(rgb)

    def chunk(tag: bytes, payload: bytes) -> bytes:
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
                     + chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + chunk(b"IEND", b""))


def cmd_add_app(args) -> None:
    data = load_fnpack()
    apps = data["apps"]
    app_id = args.app
    if app_id in apps and not args.force:
        sys.exit(f"错误：应用 {app_id} 已存在（加 --force 可覆盖索引条目，目录文件不会被覆盖）")
    cats = list(dict.fromkeys(args.cat))
    for c in cats:
        if c not in FIXED_CATEGORIES:
            sys.exit(f"错误：分类 {c} 不在固定分类中：{'、'.join(FIXED_CATEGORIES)}")
    if len(cats) > 2:
        sys.exit("错误：分类最多填 2 个，第一个为主分类")
    platforms = [p.strip() for p in args.platform.split(",") if p.strip()]
    for p in platforms:
        if p not in PLATFORMS:
            sys.exit(f"错误：platform 只允许 all/x86/arm，收到 {p}")
    if args.run_as and args.run_as not in RUN_AS_VALUES:
        sys.exit(f"错误：run_as 只允许 package 或 root，收到 {args.run_as}")

    app_dir = ROOT / app_id
    (app_dir / "Preview").mkdir(parents=True, exist_ok=True)
    icon = app_dir / "ICON.PNG"
    if not icon.exists():
        placeholder_png(icon, 256, 256)
    preview = app_dir / "Preview" / "1.png"
    if not preview.exists():
        placeholder_png(preview, 640, 360)
    readme = app_dir / "README.md"
    if not readme.exists():
        readme.write_text(
            f"# {args.name or app_id}\n\n{args.desc or '（应用介绍）'}\n\n## 使用说明\n\n（待补充）\n",
            encoding="utf-8")

    entry = {
        "display_name": args.name or app_id,
        "desc": args.desc or "",
        "platform": platforms or ["x86", "arm"],
        "categories": cats or ["系统工具"],
        "icon_url": f"{app_id}/ICON.PNG",
        "preview_urls": [f"{app_id}/Preview/1.png"],
        "readme_url": f"{app_id}/README.md",
        "releases": {},
    }
    if args.docker:
        entry["is_docker"] = True
    if args.port:
        entry["service_port"] = args.port
    if args.run_as:
        entry["run_as"] = args.run_as
    if args.install_type is not None:
        if args.install_type not in INSTALL_TYPE_VALUES:
            sys.exit("错误：install_type 只允许空字符串（存储空间）或 root（系统空间）")
        entry["install_type"] = args.install_type
    if args.maintainer:
        entry["maintainer"] = args.maintainer
        entry["maintainer_url"] = args.maintainer_url or ""
    apps[app_id] = entry
    save_fnpack(data)
    print(f"已创建应用 {app_id}：目录骨架 {app_dir}，索引条目已写入 fnpack.json")
    print("下一步：为它追加第一个版本 → add-release")


def cmd_add_release(args) -> None:
    data = load_fnpack()
    app = data["apps"].get(args.app)
    if app is None:
        sys.exit(f"错误：应用 {args.app} 不存在，先用 add-app 创建")
    sources = []
    if args.x86:
        sources.append(("x86", args.x86))
    if args.arm:
        sources.append(("arm", args.arm))
    if not sources:
        sys.exit("错误：至少提供一个 --x86 或 --arm 的 fpk 文件路径或 URL")

    owner_repo = github_owner_repo(data)
    tag = args.tag or datetime.date.today().strftime("%Y.%m.%d")
    packages = {}
    for arch, src in sources:
        p = Path(src)
        if p.is_file():
            sha, size = hash_file(p)
            if args.url_prefix:
                base = args.url_prefix.rstrip("/")
            elif owner_repo:
                base = f"https://github.com/{owner_repo[0]}/{owner_repo[1]}/releases/download/{tag}"
            else:
                base = ""
                print("警告：未提供 --url-prefix 且 homepage 未指向 GitHub 仓库，download_url 置空待补")
            packages[arch] = {"download_url": f"{base}/{p.name}", "sha256": sha, "size": size}
        elif src.startswith(("http://", "https://")):
            if args.fetch:
                print(f"正在下载以计算校验值（{arch}）：{src}")
                sha, size = fetch_remote_info(src)
            else:
                sha, size = args.sha256 or "", args.size or 0
            if not sha or not size:
                sys.exit(f"错误：URL 方式需加 --fetch 自动获取校验值，或同时提供 --sha256 和 --size（{arch}）")
            packages[arch] = {"download_url": src, "sha256": sha, "size": size}
        else:
            sys.exit(f"错误：找不到文件 {src}")

    app["releases"][args.version] = {
        "changelog": args.changelog or "",
        "updated_at": now_iso(),
        "packages": packages,
    }
    if args.os_min_version:
        app["releases"][args.version]["os_min_version"] = args.os_min_version
    save_fnpack(data)
    print(f"已写入 {args.app} {args.version}：{'/'.join(packages)}")
    if args.url_prefix:
        print(f"下载地址前缀：{args.url_prefix}")
    elif owner_repo:
        print(f"下一步：把 fpk 上传到 Releases 标签 {tag}")
        print(f"      网页 https://github.com/{owner_repo[0]}/{owner_repo[1]}/releases/new?tag={tag}")
        print(f"      或命令行：gh release create {tag} dist/*.fpk --title \"{tag}\"")


def cmd_validate(_args) -> None:
    data = load_fnpack()
    errors, warnings = [], []
    for app_id, app in data["apps"].items():
        pre = f"[{app_id}] "
        for key in ("display_name", "desc", "platform", "categories", "icon_url", "releases"):
            if key not in app:
                errors.append(pre + f"缺少必填字段 {key}")
        for p in app.get("platform", []):
            if p not in PLATFORMS:
                errors.append(pre + f"非法 platform：{p}")
        for c in app.get("categories", []):
            if c not in FIXED_CATEGORIES:
                errors.append(pre + f"非法分类：{c}")
        if len(app.get("categories", [])) > 2:
            errors.append(pre + "分类最多 2 个")
        run_as = app.get("run_as")
        if run_as not in (None, "") and run_as not in RUN_AS_VALUES:
            errors.append(pre + f"run_as 只允许 package/root，收到 {run_as}")
        inst = app.get("install_type")
        if inst not in (None, "") and inst not in INSTALL_TYPE_VALUES:
            errors.append(pre + f"install_type 只允许空串/root，收到 {inst}")
        icon_url = app.get("icon_url")
        if icon_url and not (ROOT / icon_url).is_file():
            errors.append(pre + f"图标不存在：{icon_url}")
        if app.get("readme_url") and not (ROOT / app["readme_url"]).is_file():
            warnings.append(pre + f"README 不存在：{app['readme_url']}")
        for pv in app.get("preview_urls", []):
            if not (ROOT / pv).is_file():
                warnings.append(pre + f"预览图不存在：{pv}")
        rels = app.get("releases", {})
        if not rels:
            warnings.append(pre + "还没有任何 release")
        for ver, rel in rels.items():
            rpre = pre + f"release {ver}: "
            if not rel.get("changelog"):
                warnings.append(rpre + "缺少 changelog")
            for arch, pkg in rel.get("packages", {}).items():
                if arch not in PLATFORMS:
                    errors.append(rpre + f"非法架构 {arch}")
                    continue
                url = pkg.get("download_url", "")
                if not url.startswith("https://"):
                    errors.append(rpre + f"{arch} download_url 缺失或不是 https")
                if not re.fullmatch(r"[0-9a-f]{64}", pkg.get("sha256", "")):
                    errors.append(rpre + f"{arch} sha256 格式非法")
                size = pkg.get("size")
                if not isinstance(size, int) or size <= 0:
                    errors.append(rpre + f"{arch} size 非法")

    for line in errors:
        print("ERROR " + line)
    for line in warnings:
        print("WARN  " + line)
    print(f"\n共 {len(data['apps'])} 个应用，{len(errors)} 个错误，{len(warnings)} 个警告")
    sys.exit(1 if errors else 0)


def cmd_gen_readme(_args) -> None:
    data = load_fnpack()
    apps = data["apps"]
    buckets: dict[str, list] = {label: [] for label, _ in GROUP_LETTERS}
    other: list = []
    for app_id, app in sorted(apps.items(), key=lambda kv: kv[0].lower()):
        ch = app_id[0].lower()
        for label, letters in GROUP_LETTERS:
            if ch in letters:
                buckets[label].append((app_id, app))
                break
        else:
            other.append((app_id, app))

    sections = []
    total = 0
    for label, _ in GROUP_LETTERS:
        items = buckets[label]
        if not items:
            continue
        total += len(items)
        rows = "\n".join(
            f"| {app_id} | {app.get('display_name', '')} | {app.get('desc', '')} |"
            for app_id, app in items)
        sections.append(f"### {label}（{len(items)} 个应用）\n\n"
                        "| 包名 | 显示名 | 描述 |\n|------|--------|------|\n" + rows)
    if other:
        total += len(other)
        rows = "\n".join(
            f"| {app_id} | {app.get('display_name', '')} | {app.get('desc', '')} |"
            for app_id, app in other)
        sections.append(f"### 其他（{len(other)} 个应用）\n\n"
                        "| 包名 | 显示名 | 描述 |\n|------|--------|------|\n" + rows)

    body = (f"\n以下根据 `fnpack.json` 自动生成（命令：`py scripts/depot.py gen-readme`，"
            f"CI 会在每次推送后自动刷新）：\n\n共 **{total}** 个应用。\n\n"
            + "\n\n".join(sections) + "\n")

    text = README_PATH.read_text(encoding="utf-8")
    start = text.find("<!-- APPS-TABLE-START -->")
    end = text.find("<!-- APPS-TABLE-END -->")
    if start == -1 or end == -1:
        text = text.rstrip("\n") + "\n\n<!-- APPS-TABLE-START -->\n" + body + "<!-- APPS-TABLE-END -->\n"
    else:
        text = text[:start] + "<!-- APPS-TABLE-START -->\n" + body + text[end:]
    README_PATH.write_text(text, encoding="utf-8")
    print(f"README 应用表已更新（{total} 个应用）")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="fnOS 应用源（fnpack.json）维护工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("add-app", help="新建应用：生成目录骨架并写入 fnpack.json")
    p.add_argument("app", help="应用包名（须与 fpk 内 manifest 的 appname 一致）")
    p.add_argument("--name", help="显示名")
    p.add_argument("--desc", help="描述（建议带一个 emoji 开头）")
    p.add_argument("--cat", action="append", default=[], help="分类，最多 2 个；默认 系统工具")
    p.add_argument("--platform", help="支持架构，逗号分隔，如 x86 / x86,arm / all；默认 x86,arm")
    p.add_argument("--port", help="服务端口")
    p.add_argument("--run-as", help="运行用户：package 或 root")
    p.add_argument("--install-type", help="安装位置：空为存储空间，root 为系统空间")
    p.add_argument("--docker", action="store_true", help="标记为 Docker 重新打包")
    p.add_argument("--maintainer", help="上游原作者/项目名")
    p.add_argument("--maintainer-url", help="上游项目主页")
    p.add_argument("--force", action="store_true", help="已存在时覆盖索引条目")
    p.set_defaults(func=cmd_add_app)

    p = sub.add_parser("add-release", help="为应用追加一个版本记录")
    p.add_argument("app", help="应用包名")
    p.add_argument("version", help="版本号，如 1.0.0")
    p.add_argument("--x86", help="x86 架构 fpk 的本地路径或 URL")
    p.add_argument("--arm", help="arm 架构 fpk 的本地路径或 URL")
    p.add_argument("--tag", help="GitHub Releases 标签，默认今天（YYYY.M.D）")
    p.add_argument("--url-prefix", help="覆盖下载地址前缀（fpk 托管在任意仓库/站点时使用）")
    p.add_argument("--changelog", help="更新说明")
    p.add_argument("--os-min-version", help="最低 fnOS 系统版本，如 1.1.3107")
    p.add_argument("--sha256", help="URL 方式手工提供的 sha256")
    p.add_argument("--size", type=int, help="URL 方式手工提供的文件大小（字节）")
    p.add_argument("--fetch", action="store_true", help="下载 URL 内容自动计算 sha256 与 size")
    p.set_defaults(func=cmd_add_release)

    sub.add_parser("validate", help="校验 fnpack.json 与目录完整性").set_defaults(func=cmd_validate)
    sub.add_parser("gen-readme", help="根据 fnpack.json 重新生成 README 应用表").set_defaults(func=cmd_gen_readme)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
