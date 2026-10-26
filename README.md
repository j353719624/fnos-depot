# fnos-depot — 飞牛 OS 应用源

飞牛 OS（fnOS）**外部应用源**仓库，索引文件为 `fnpack.json`（schema v2），支持 x86 / arm 双版本。

仓库只放元数据和展示图片，fpk 安装包托管在 GitHub Releases，更新用脚本和 CI 自动维护。

## 目录结构

```
fnos-depot/
├── fnpack.json            # 应用源索引（核心，飞牛客户端读取的就是它）
├── README.md              # 本文件，含自动生成的应用总表
├── scripts/depot.py       # 维护工具：建条目 / 发版本 / 校验 / 生成表格
├── .github/workflows/     # CI：每次推送自动校验并刷新 README 应用表
└── <应用包名>/             # 每个应用一个目录
    ├── ICON.PNG           # 256x256 图标
    ├── Preview/1.png      # 预览截图
    └── README.md          # 应用介绍
```

## 在飞牛 OS 上添加本源

应用中心 → 外部应用源，最简单直接填仓库根地址：

```
https://github.com/j353719624/fnos-depot
```

客户端会读取仓库默认分支根目录的 `fnpack.json`。如果客户端无法直连 GitHub，可改用 JSON 直链并加加速前缀：

```
https://gh-proxy.com/https://raw.githubusercontent.com/j353719624/fnos-depot/main/fnpack.json
```

## fpk 安装包放在哪里

两种方式都符合规范，按应用实际情况选择：

1. **GitHub Releases（推荐）**：fpk 传到应用自己仓库的 Releases，`download_url` 写绝对地址。仓库保持轻量，`add-release` 默认就是这种模式。
2. **仓库内相对路径**：fpk 直接提交进本仓库（如 `<应用>/fpk/xxx.fpk`），`download_url` 写 `./<应用>/fpk/xxx.fpk`。相对地址跟随 fnpack.json 的访问地址解析，配合加速前缀时下载也会走加速。`add-release --url-prefix` 可把下载地址指向任意仓库或站点。

已发布的「版本号 + 架构」安装包视为不可变：内容有变更必须发新版本号，不能静默替换同版本文件，否则 sha256 校验会导致老用户无法更新。

## 发布一个应用的完整流程

以 `hello-world` 为例（fpk 需自行用官方打包工具制作，或从上游项目获取）：

```bash
# 1. 新建应用：生成目录骨架 + 写入索引条目
py scripts/depot.py add-app hello-world --name "示例应用" --desc "🚀第一个示例" --cat 系统工具

# 2. 把 fpk 上传到 GitHub Releases（标签按日期，如 2026.10.27）
#    网页：https://github.com/j353719624/fnos-depot/releases/new?tag=2026.10.27
#    或命令行：gh release create 2026.10.27 dist/*.fpk --title "2026.10.27"

# 3. 写入版本记录（本地 fpk 自动算 sha256 和大小，生成下载链接）
py scripts/depot.py add-release hello-world 1.0.0 \
    --x86 dist/hello-world-1.0.0-x86.fpk --arm dist/hello-world-1.0.0-arm.fpk \
    --changelog "初始版本"

# 4. 提交推送，CI 会自动校验并刷新 README 应用表
git add -A && git commit -m "chore: release hello-world 1.0.0" && git push
```

`add-release` 也支持已托管在别处的 URL：加 `--url-prefix` 指定下载地址前缀（fpk 在其他仓库 Releases 时用），或加 `--fetch` 自动下载远端文件计算校验值，或手工提供 `--sha256` / `--size`。

## 常用命令

| 命令 | 作用 |
|------|------|
| `py scripts/depot.py add-app <包名> ...` | 新建应用条目和目录骨架 |
| `py scripts/depot.py add-release <包名> <版本> ...` | 追加一个版本（自动算 sha256/size） |
| `py scripts/depot.py validate` | 校验索引与目录完整性（CI 也会跑） |
| `py scripts/depot.py gen-readme` | 重新生成下方应用总表 |

固定分类（与飞牛商店一致，不可自造）：`影音娱乐`、`系统工具`、`编程开发`、`AI赋能`、`生活服务`、`智能智控`、`教育学习`、`游戏地带`、`硬件驱动`。每个应用最多填 2 个分类，第一个为主分类。

## 应用列表

<!-- APPS-TABLE-START -->

以下根据 `fnpack.json` 自动生成（命令：`py scripts/depot.py gen-readme`，CI 会在每次推送后自动刷新）：

共 **1** 个应用。

### M–R（1 个应用）

| 包名 | 显示名 | 描述 |
|------|--------|------|
| mercury | MERCURY | MERCURY 是运行在 fnOS 上的交换机集中管理应用。通过 fnOS 即可对家庭与中小企业网络中的交换机进行设备发现、状态监控、配置下发与诊断运维，让 NAS 成为整张网络的管理入口。 |
<!-- APPS-TABLE-END -->
