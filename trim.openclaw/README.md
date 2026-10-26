# openclaw-fnos

飞牛 fnOS 非官方社区版 OpenClaw 应用包(fpk)的构建源。自带 node 26.10 + bun 1.4.2 运行时,零依赖、可离线安装。

> 下载现成的 fpk 包请到 [Releases](../../releases)。

## 包内包含

- OpenClaw **2026.9.4**(npmmirror 拉取)
- 全部壳补丁(见下)
- claw-approve 设备配对自动批准脚本 + 安装时自动配置 5 秒 systemd 定时器
- `openclaw-gateway.service` 网关单元(安装时写入并 enable,重启 NAS 后网关自动启动)
- root 运行自愈(重装/换机后自动恢复 root,详见下文)

## 壳补丁清单(server/index.js)

1. 进程识别(sigfix):壳的停止逻辑此前不识别预热期的 `npm install` / vendor node 子进程,导致 `Refusing to signal`、重装后残留孤儿进程占住状态目录。已扩展 `isLikelyOpenclawProcess` 的匹配模式。
2. 渠道插件钉**具体版本**(feishu/wecom/dingtalk/weixin/qqbot),重启不再全量重装插件(重启约 15~20 秒就绪)。
3. 插件安装命令统一带 `--force --accept-capabilities`(OpenClaw 2026.9 安全门)。
4. 代理请求 XFF 修正(去除 loopback、合成 NAS 内网 IP,解决 `proxy_attribution_required` 403)。
5. Bun fetch 自动解压后仍保留 `content-encoding: br` 标签导致的浏览器白页修复。
6. 移除新版 OpenClaw 拒绝的旧配置键(`controlUi.allowInsecureAuth`、`config.cli`)。

## 生命周期脚本(cmd/)

- `install_callback`:预装 OpenClaw 核心 → 配置 5 秒配对自动批准定时器 → **root 强制**(包内 privilege 为 root 时,重写运行时 privilege 并 chown 数据/应用目录)
- `cmd/main`:`enforce_root_runas()` 自愈——每次启动检查"包要求 root 但框架把运行时配置重置回普通用户"的情况,通过免密 sudo 提权重入并修复;开头自举 TRIM_* 环境变量(框架不注入时用默认路径);运行时按安装卷自动定位(pkg/vendor/runtime),并把**包内自带的 node/bun 置于 PATH 最前**,避免按名字解析到 fnOS 的 `nodejs_v24`(v24.15.0,存在 `node:sqlite` 截断 TEXT 的已知缺陷 nodejs/node#61954)

## 目录结构

```
source/pkg-trim.openclaw/
├── manifest            # fpk 清单(checksum 为 app.tgz 的 md5)
├── cmd/                # 生命周期脚本(install_callback / main / openclaw-gateway.service 等)
├── config/             # privilege 模板、claw-approve、bootstrap 种子、prompts
├── ui/  wizard/        # 桌面入口与安装向导
├── ICON.PNG  ICON_256.PNG
└── pkg/                # app.tgz 的内容
    ├── server/index.js # 壳(含全部补丁)
    ├── config/         # 随包运行时配置(privilege 在打包时按变体覆盖)
    ├── bin/            # (不入库)openclaw 包装脚本,install 时生成
    └── vendor/         # (不入库)node/bun 运行时,构建前准备
```

## 构建(在 fnOS NAS 上)

1. 准备运行时(仅首次):
   - 下载 [node v26.10.0 linux-x64](https://registry.npmmirror.com/-/binary/node/v26.10.0/node-v26.10.0-linux-x64.tar.xz) 解压到 `pkg/vendor/runtime/node`
   - 下载 [bun 1.4.2](https://registry.npmmirror.com/-/binary/bun/v1.4.2/bun-linux-x64.zip) 解压到 `pkg/vendor/runtime/bun-bin`
2. 把本仓库 `source/pkg-trim.openclaw/` 放到 NAS(如 `/vol2/1000/workspace/FPK/SOURCE/pkg-trim.openclaw`)
3. 运行 `./build.sh /源目录 /输出目录 [版本号]`,产物为 `root` / `user` 两个变体 fpk

`build.sh` 做的事:按变体写 `config/privilege` → `tar pkg/` 为 app.tgz → 计算 md5 回填 manifest → 打包 fpk。

## 安装

```
appcenter-cli manual-install enable   # 或应用中心侧边栏开关
# 应用中心 → 手动安装 → 上传 fpk
```

- **root 变体(推荐)**:以 root 运行;框架重装后若把用户重置回普通用户,启动脚本会通过免密 sudo 自愈(需要一次性的 sudoers 配置:`trim.openclaw ALL=(root) NOPASSWD: /var/apps/trim.openclaw/cmd/main`)
- **user 变体**:以包用户运行,插件目录属主由 claw-approve 定时器自动修正

## ⚠️ 注意

- **卸载或安装失败回滚会清空应用数据**(会话、渠道账号、模型配置、设备配对),先备份 `@apphome`
- 首次启动(或清数据后)会全量下载渠道插件,预热几分钟属正常;之后重启约 20 秒
- 模型配置(API Key)不在包内:`config/bootstrap/openclaw.json.seed` 是首装种子模板,凭据处为占位符,装后在 WebUI 配置
- 依赖内网隧道的模型端点(如公司推理服务),换机器需重新登录组网工具

