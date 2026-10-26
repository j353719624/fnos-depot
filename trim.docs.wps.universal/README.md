# Office文档 WPS 通用版

这是面向 fnOS x86_64 的通用版 WPS GUI 适配包。它把 Xtigervnc、xwininfo、websockify、noVNC 和所需的 X11 运行库放进 FPK，启动时自动识别 fnOS 上的非 root 用户、存储卷和可用端口。

## 构建

在包含基础 WPS FPK 的目录执行：

```powershell
python .\generic-version\repack_generic.py
```

默认读取上级目录的 `trim.docs.wps_0.1.0_x86.fpk`，生成 `trim.docs.wps_universal_0.2.0_x86_64.fpk`。

## 安装

```bash
sudo appcenter-cli install-fpk trim.docs.wps_universal_0.2.0_x86_64.fpk
sudo appcenter-cli start trim.docs.wps.universal
```

桌面文件管理器入口使用 `/docs-wps-universal/preview`。默认服务端口为 10602，端口被占用时会自动选择备用端口；noVNC 默认使用 10603，控制接口默认使用 10604。

## 适用范围

目标仍是 fnOS x86_64，因为 WPS Linux 引擎本身是 amd64 二进制。通用版解决的是用户、安装卷、宿主缺少 VNC/noVNC 组件以及端口冲突，不包含 ARM 版本 WPS 引擎。

已发布 Release：v0.2.2。


