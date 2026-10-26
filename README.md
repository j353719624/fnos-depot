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

应用中心 → 外部应用源，填入：

```
https://raw.githubusercontent.com/j353719624/fnos-depot/main/fnpack.json
```

国内网络如无法直连 raw.githubusercontent.com，可加加速前缀：

```
https://gh-proxy.com/https://raw.githubusercontent.com/j353719624/fnos-depot/main/fnpack.json
```

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

`add-release` 也支持已托管在别处的 URL：加 `--fetch` 自动下载计算校验值，或手工提供 `--sha256` / `--size`。

## 常用命令

| 命令 | 作用 |
|------|------|
| `py scripts/depot.py add-app <包名> ...` | 新建应用条目和目录骨架 |
| `py scripts/depot.py add-release <包名> <版本> ...` | 追加一个版本（自动算 sha256/size） |
| `py scripts/depot.py validate` | 校验索引与目录完整性（CI 也会跑） |
| `py scripts/depot.py gen-readme` | 重新生成下方应用总表 |

固定分类（与飞牛商店一致，不可自造）：`AI赋能`、`影音娱乐`、`教育学习`、`智能智控`、`游戏地带`、`生活服务`、`系统工具`、`编程开发`。

## 应用列表

<!-- APPS-TABLE-START -->

以下根据 `fnpack.json` 自动生成（命令：`py scripts/depot.py gen-readme`，CI 会在每次推送后自动刷新）：

共 **0** 个应用。


<!-- APPS-TABLE-END -->
